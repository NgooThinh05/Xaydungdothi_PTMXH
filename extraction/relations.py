"""Trích xuất quan hệ từ tin tức bằng luật (trigger + ràng buộc kiểu thực thể + khoảng cách).

Đầu vào : data/interim/news_docs.jsonl (preprocess/build_corpus.py)
Đầu ra  : data/processed/edges_news.csv           cạnh đã gộp (src, rel, dst) – weight = số lần xuất hiện
          data/processed/nodes_person_news.csv    người mới phát hiện từ tin tức
          data/processed/nodes_org_news.csv       cơ quan mới (chủ yếu cấp tỉnh)
          data/interim/relation_mentions.jsonl    từng lần trích (câu bằng chứng) – dùng để đánh giá
          data/eval/sample_to_label.csv           200 cạnh mẫu phân tầng theo loại để gán nhãn thủ công

Mỗi luật: trigger regex, kiểu chủ thể (trước trigger), kiểu đối tượng (sau trigger), khoảng cách tối đa,
khoảng trống hợp lệ giữa trigger và đối tượng, dạng bị động ("được/bị ... "), và các mẫu loại trừ.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ner_link import DocContext, Linker, Mention, analyse_sentence  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"
EVAL = ROOT / "data" / "eval"

P, O = "PER", "ORG"
LIST_RELS = {"BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM", "KY_LUAT", "KIEM_TRA"}


@dataclass
class Rule:
    rel: str
    trigger: str
    subj: tuple            # kiểu chủ thể cho phép
    obj: tuple             # kiểu đối tượng cho phép
    subj_win: int = 160    # ký tự tối đa từ cuối chủ thể tới trigger
    obj_win: int = 60      # ký tự tối đa từ trigger tới đầu đối tượng
    obj_gap: str = r".*"   # regex fullmatch cho đoạn chữ giữa trigger và đối tượng
    subj_gap_bad: str = r"[;:]|\. "   # không vượt qua dấu này giữa chủ thể và trigger
    neg_before: str = ""   # loại nếu ngay trước trigger khớp (…$)
    neg_after: str = ""    # loại nếu ngay sau trigger khớp (^…)
    passive: bool = False  # cho phép "<đối tượng> được/bị <trigger>"
    conf: float = 0.9
    subj_gap: str = ""     # regex fullmatch cho đoạn giữa chủ thể và trigger (rỗng = không ràng buộc)


GAP_SHORT = r"\s*(?:cho |các |đối với |với |ngay |đồng chí |ông |bà |trực tiếp |lãnh đạo )*\s*"
RULES = [
    Rule("CHU_TRI", r"chủ trì", (P,), (O,), obj_win=90,
         obj_gap=r"(?:(?!;|\. |, |nghị quyết|Nghị quyết|quyết định|chỉ thị|kết luận của).)*", neg_after=r"^,|^\s*(?:và|,)", neg_before=r"(?:giao|đơn vị|cơ quan|là|được)\s*$"),
    Rule("CHI_DAO", r"chỉ đạo|yêu cầu|đề nghị|giao", (P,), (O, P), subj_win=45, obj_win=40, obj_gap=GAP_SHORT,
         neg_before=r"(?:Ban|sự|theo|Theo|phát biểu|Phát biểu|dự và|lãnh đạo,|lãnh đạo và|được|đã được|bàn|ngoại|Ngoại|Đoàn|Tổ|chuyển|trao|"
                    r"kết luận,|ý kiến|đúng|nội dung|các|những|nhiệm vụ được|thực hiện)\s*$",
         neg_after=r"^\s*(?:thông|dịch|lưu|ban|tiếp|thương|hữu|nhận|kết|nộp|đất|việc|của|tại|quyết liệt|,)", conf=0.85),
    Rule("BO_NHIEM", r"(?:trao )?(?:quyết định )?(?:bổ nhiệm(?: lại)?|phê chuẩn(?: việc)?(?: bổ nhiệm)?|chỉ định|phân công)",
         (P, O), (P,), subj_win=200, obj_win=120, obj_gap=r"(?:(?!;|\. | cho ).)*", passive=True,
         neg_before=r"(?:quy trình|công tác|việc|về|thẩm quyền|tiêu chuẩn|sự|được giao|nhiệm vụ|không|chưa)\s*$",
         neg_after=r"^\s*(?:kết quả\s+)?(?:miễn nhiệm|cho thôi|bãi nhiệm|miễn)"),
    Rule("DIEU_DONG", r"điều động(?:, bổ nhiệm)?|luân chuyển|biệt phái", (O, P), (P,), subj_win=200, obj_win=100,
         obj_gap=r"(?:(?!;|\. ).)*", passive=True, neg_before=r"(?:công tác|việc|về)\s*$",
         neg_after=r"^\s*(?:lực lượng|phương tiện|xe|máy|cán bộ,|các|nhân lực|\d)"),
    Rule("MIEN_NHIEM", r"miễn nhiệm|bãi nhiệm|cho thôi giữ chức(?: vụ)?|thôi giữ chức(?: vụ)?|cho thôi làm|cho nghỉ hưu|"
                       r"cho thôi tham gia", (O, P), (P,), subj_win=200, obj_win=80, obj_gap=r"(?:(?!;|\. ).)*",
         passive=True, neg_before=r"(?:việc|về|không|chưa|không thực hiện thủ tục|không thực hiện)\s*$"),
    Rule("THANH_TRA", r"[Kk]ết luận thanh tra|[Qq]uyết định thanh tra|thanh tra|kiểm toán", (O,), (O,), subj_win=150, obj_win=100,
         obj_gap=r"(?:(?!;|\. |chỉ đạo|theo |xử lý |năm \d).){0,140}?(?:tại|đối với|trách nhiệm của|trách nhiệm|của)\s*(?:các |Ban Thường vụ |Ban cán sự đảng |Ban Giám đốc )?", neg_before=r"(?:Thanh tra|Tổng|Phó Tổng|Đoàn|đoàn|Kiểm toán|cơ quan|Cơ quan|"
                                              r"Chánh|Phó Chánh|kết luận|Kết luận|công tác|ngành)\s*$",
         neg_after=r"^\s*(?:viên|Chính phủ|Nhà nước|nhà nước|tỉnh|thành phố|Bộ|bộ|khu vực)\b", conf=0.85),
    Rule("KIEM_TRA", r"kiểm tra|giám sát", (O, P), (O, P), subj_win=120, obj_win=110,
         obj_gap=r"(?:\s*(?:,\s*giám sát\s*)?|(?:(?!;|\. |chỉ đạo|theo |của ).){0,90}?(?:đối với|tại)\s*)(?:các |Ban Thường vụ |Ban cán sự đảng |Đảng đoàn |Thường trực |tổ chức đảng |đồng chí )?\s*", neg_before=r"(?:Ủy ban|Đoàn|đoàn|Ban|Tổ|Chủ nhiệm|Phó Chủ nhiệm|ủy ban|công tác|"
                                             r"cơ quan|và|,)\s*$",
         neg_after=r"^\s*(?:viên|,\s*làm việc|và làm việc)", conf=0.85),
    Rule("KY_LUAT", r"thi hành kỷ luật|kỷ luật|cảnh cáo|khiển trách|cách chức|cách tất cả các chức vụ|khai trừ(?: ra)?(?: khỏi Đảng)?",
         (O, P), (P,), subj_win=200, obj_win=90, obj_gap=r"(?:(?!;|\. ).)*", passive=True,
         neg_before=r"(?:Hội đồng|hình thức|kỷ cương,|kỷ luật,|biện pháp|ý thức|tính)\s*$",
         neg_after=r"^\s*(?:,\s*kỷ cương|kỷ cương|lao động|tài chính|Đảng là|của Đảng)"),
    Rule("LAM_VIEC_VOI", r"(?:thăm và |kiểm tra và |thăm, )?làm việc (?:với|tại)|hội kiến|tiếp xã giao", (P,), (O,),
         subj_win=200, obj_win=50, obj_gap=r"\s*(?:các |lãnh đạo |Ban Thường vụ |Ban cán sự đảng |Thường trực |Đảng ủy )*\s*",
         neg_before=r"(?:buổi|cuộc|khi|thời gian|chương trình|trong)\s*$"),
    Rule("PHOI_HOP", r"phối hợp(?: chặt chẽ)? với|ký kết quy chế phối hợp(?: công tác)?(?: với)?|ký kết chương trình phối hợp(?: với)?|"
                     r"ký quy chế phối hợp(?: với)?|ký kết thỏa thuận hợp tác(?: với)?", (O,), (O,), subj_win=70, obj_win=40,
         obj_gap=r"\s*(?:các |giữa )?\s*", neg_before=r"(?:sự|việc|cơ chế|được)\s*$",
         subj_gap=r"\s*,?\s*(?:(?:đã|sẽ|cần|tiếp tục|chủ động|có trách nhiệm|chủ trì,?|đang|cũng|thường xuyên|trực tiếp|"
                  r"tích cực|khẩn trương|và|đồng thời)\s*,?\s*)*"),
]
for r in RULES:
    r.trig_re = re.compile(r"(?<![\w])(?:" + r.trigger + r")(?![\w])")
    r.neg_b = re.compile(r.neg_before) if r.neg_before else None
    r.neg_a = re.compile(r.neg_after) if r.neg_after else None
    r.gap_re = re.compile(r.obj_gap)
    r.bad_re = re.compile(r.subj_gap_bad)

MEETING_RE = re.compile(r"\s*(?:(?:buổi|cuộc|phiên) )?(?:họp|hội nghị|Hội nghị|phiên họp|Phiên họp|cuộc họp|buổi làm việc|hội thảo|"
                        r"Hội thảo|tọa đàm|Tọa đàm|đối thoại|giao ban|phiên thảo luận|Phiên thảo luận|lễ|Lễ|"
                        r"buổi tiếp|cuộc làm việc|hội nghị trực tuyến)")
PASSIVE_RE = re.compile(r"(?:được|bị|vừa được|vừa bị|đã được|đã bị|sẽ được|sẽ bị)\s*(?:Bộ Chính trị |Ban Bí thư |Thủ tướng )?$")
AGENT_RE = re.compile(r"^\s*(?:[^,;]{0,60}?)\b(?:bởi|do)\s*$")
NOT_SUBJ_RE = re.compile(r"(?:Theo|theo|của|với|cho|tại|Tại|trình|gửi|đối với|giữa|và|cùng)\s*$")
DECISION_OF_RE = re.compile(r"(?:[Qq]uyết định|[Nn]ghị quyết|[Tt]hông báo|[Kk]ết luận|[Cc]hỉ thị)(?: số [^ ,]+)?(?: ngày [^ ,]+)?(?: của)\s*$")
PRESENTER_RE = re.compile(r"trình bày|[Tt]ờ trình|dự thảo|công bố|trao|đọc|thông qua|đề nghị cấp có thẩm quyền|báo cáo")
NO_INTERVENE = {"CHI_DAO", "CHU_TRI", "LAM_VIEC_VOI", "PHOI_HOP"}
AGENT_RELS = {"BO_NHIEM", "DIEU_DONG", "MIEN_NHIEM", "KY_LUAT"}
CONNECT_RE = re.compile(r"[\s,]*(?:(?:điều động|luân chuyển|phân công|quyết định|đồng ý|chuẩn y|phê chuẩn|bầu|chỉ định|"
                        r"giới thiệu|và|vừa|đã|chính thức)[\s,]*)*")
SPEECH_RE = re.compile(r"cho biết|cho rằng|nhấn mạnh|khẳng định|nói|chia sẻ|phát biểu|đánh giá|lưu ý|cho hay|thông tin")


def inside(pos: int, ms: list[Mention]) -> bool:
    return any((m.span[0] if m.kind == P and m.span else m.start) <= pos < (m.span[1] if m.kind == P and m.span else m.end)
               for m in ms)


def args(ms: list[Mention], kinds: tuple):
    return [m for m in ms if m.kind in kinds and not m.absorbed]


def extract_sentence(s: str, ms: list[Mention]):
    out = []
    for rule in RULES:
        for t in rule.trig_re.finditer(s):
            ta, tb = t.start(), t.end()
            if inside(ta, ms):  # trigger nằm trong tên cơ quan / cụm chức danh
                continue
            if rule.neg_b and rule.neg_b.search(s[max(0, ta - 30):ta]):
                continue
            if rule.neg_a and rule.neg_a.search(s[tb:tb + 30]):
                continue
            subj = obj = None
            is_passive = False
            if rule.passive:
                pv = list(re.finditer(r"(?<![\w])(?:được|bị)(?![\w])", s[max(0, ta - 90):ta]))
                if pv:
                    pa = max(0, ta - 90) + pv[-1].end()
                    between = [m for m in ms if m.start >= pa and m.end <= ta and not m.absorbed]
                    rest = s[pa:ta]
                    for m in sorted(between, key=lambda x: -x.start):
                        rest = rest[:m.start - pa] + rest[(m.span[1] if m.kind == P and m.span else m.end) - pa:]
                    if CONNECT_RE.fullmatch(rest):
                        is_passive = True
                        agents = [m for m in between if m.kind in rule.subj]
            if is_passive:
                # "<P> (vừa) được [<tác nhân>] [điều động,] bổ nhiệm ..." -> đối tượng đứng trước "được"
                cands = [m for m in args(ms, rule.obj) if m.end <= pa and pa - (m.span[1] if m.kind == P and m.span else m.end) <= 120
                         and not rule.bad_re.search(s[m.end:pa])]
                if not cands:
                    continue
                obj = cands[-1]
                if agents:
                    subj = agents[-1]
                else:
                    ag = [m for m in args(ms, (O,)) if O in rule.subj and m.end <= obj.start and obj.start - m.end <= rule.subj_win
                          and m.id != obj.id and not rule.bad_re.search(s[m.end:obj.start])]
                    subj = ag[-1] if ag else None
                if subj is None:
                    continue
            else:
                cands = []
                for m in args(ms, rule.subj):
                    m_end = m.span[1] if m.kind == P and m.span else m.end
                    m_beg = m.span[0] if m.kind == P and m.span else m.start
                    if not (m.end <= ta and ta - m_end <= rule.subj_win and not rule.bad_re.search(s[m_end:ta])):
                        continue
                    pre = s[max(0, m_beg - 40):m_beg]
                    if NOT_SUBJ_RE.search(pre[-12:]) and not (rule.rel in AGENT_RELS and DECISION_OF_RE.search(pre)):
                        continue
                    if SPEECH_RE.search(s[m_end:ta]):
                        continue
                    if rule.rel in AGENT_RELS and PRESENTER_RE.search(s[m_end:ta]):
                        continue  # người trình bày / công bố quyết định không phải tác nhân
                    if rule.subj_gap and not re.fullmatch(rule.subj_gap, s[m_end:ta]):
                        continue
                    if rule.rel in NO_INTERVENE and any(o is not m and not o.absorbed and m_end <= o.start and o.end <= ta
                                                         for o in ms):
                        continue
                    if rule.rel == "PHOI_HOP" and m.via == "title":
                        continue
                    cands.append(m)
                if not cands:
                    continue
                subj = cands[-1]
                after = [m for m in args(ms, rule.obj) if m.start >= tb and m.start - tb <= rule.obj_win and m.id != subj.id]
                for m in after:
                    gap = s[tb:(m.span[0] if m.kind == P and m.span else m.start)]
                    if rule.gap_re.fullmatch(gap):
                        obj = m
                    break
                if obj is None and rule.rel == "CHU_TRI" and subj.kind == P and subj.roles \
                        and MEETING_RE.match(s[tb:tb + 40]):
                    # "X, Chủ tịch UBND tỉnh Y chủ trì cuộc họp ..." -> cơ quan của người chủ trì (ưu tiên chức vụ cụ thể)
                    GENERIC = {"org:ban_chap_hanh_trung_uong_dang", "org:bo_chinh_tri", "org:ban_bi_thu", "org:quoc_hoi"}
                    spec = [o for _, o in subj.roles if o not in GENERIC]
                    if spec:
                        obj = Mention(O, -1, -1, "", spec[0], conf=0.8, via="self_org")
                if obj is None:
                    continue
            if subj.id == obj.id:
                continue
            if rule.rel == "THANH_TRA" and not re.search(r"thanh_tra|kiem_toan|uy_ban_kiem_tra", subj.id):
                continue
            if rule.rel == "THANH_TRA" and re.match(r"(?:(?!trách nhiệm).)*của\s*$", s[tb:obj.start]) and "kết luận" not in t.group(0):
                continue
            props = {}
            if rule.rel in ("BO_NHIEM", "DIEU_DONG"):
                tail = s[max(obj.end, tb):][:160]
                rm = re.search(r"(?:giữ chức(?: vụ)?|giữ chức danh|làm|đến nhận công tác tại|về công tác tại|đến công tác tại|tham gia)\s+", tail)
                if rm:
                    later = [m for m in ms if m.kind == O and m.start >= max(obj.end, tb) + rm.end()]
                    if later:
                        props["to_org"] = later[0].id
                        role = s[max(obj.end, tb) + rm.end():later[0].start].strip(" ,")
                        props["role"] = role if len(role) <= 40 and "," not in role else ""
            objs = [obj]
            if obj.kind == P and is_passive and rule.rel in LIST_RELS:
                nxt = obj
                for m in reversed([m for m in ms if m.kind == P and m.end <= (obj.span[0] if obj.span else obj.start)]):
                    if m.id == subj.id:
                        break
                    if re.fullmatch(r"\s*(?:,|;|và|,\s*và)?\s*(?:ông|bà|đồng chí)?\s*", s[(m.span[1] if m.span else m.end):(nxt.span[0] if nxt.span else nxt.start)]):
                        objs.append(m); nxt = m
                    else:
                        break
            if obj.kind == P and not is_passive and rule.rel in LIST_RELS:
                prev = obj
                for m in [m for m in ms if m.kind == P and m.start > obj.start]:
                    pe = prev.span[1] if prev.span else prev.end
                    if re.fullmatch(r"\s*(?:,|;|và|,\s*và)?\s*(?:ông|bà|đồng chí)?\s*", s[pe:(m.span[0] if m.span else m.start)]):
                        objs.append(m); prev = m
                    else:
                        break
            for ob in objs:
                conf = min(subj.conf, ob.conf, rule.conf)
                out.append({"rel": rule.rel, "src": subj.id, "src_label": "Person" if subj.kind == P else "Organization",
                            "dst": ob.id, "dst_label": "Person" if ob.kind == P else "Organization",
                            "trigger": t.group(0), "conf": round(conf, 2), "src_text": subj.text, "dst_text": ob.text,
                            "passive": bool(is_passive), **props})
    # KIEM_TRA dạng "Đoàn kiểm tra, giám sát số 24 của Bộ Chính trị, Ban Bí thư ... làm việc với Ban Thường vụ Tỉnh ủy X"
    for t in re.finditer(r"(?<![\w])[Đđ]oàn (?:[Kk]iểm tra|[Gg]iám sát|[Kk]iểm tra, giám sát)(?: (?:số )?\d+)?(?: của)?\s+", s):
        owners, pos = [], t.end()
        for m in [m for m in ms if m.kind == O and m.start >= pos]:
            if re.fullmatch(r"\s*(?:,|và)?\s*", s[pos:m.start]):
                owners.append(m); pos = m.end
            else:
                break
        if not owners:
            continue
        tgt = re.search(r"(?:làm việc với|kiểm tra|giám sát|công bố quyết định kiểm tra(?:, giám sát)? (?:đối với|tại)|"
                        r"thông qua (?:dự thảo )?(?:báo cáo|thông báo) kết quả (?:kiểm tra|giám sát)(?:[^;.]{0,40}?)(?:đối với|tại))\s*"
                        r"(?:các |Ban Thường vụ |Ban cán sự đảng |Đảng đoàn |Thường trực )?", s[pos:])
        if not tgt:
            continue
        ta = pos + tgt.end()
        dst = next((m for m in ms if m.kind == O and m.start == ta), None)
        if dst is None:
            continue
        for ow in owners:
            if ow.id != dst.id:
                out.append({"rel": "KIEM_TRA", "src": ow.id, "src_label": "Organization", "dst": dst.id,
                            "dst_label": "Organization", "trigger": "doan_kiem_tra", "conf": 0.9, "src_text": ow.text,
                            "dst_text": dst.text, "passive": False})
    # PHOI_HOP dạng "<O1> và <O2> ký kết quy chế phối hợp"
    for t in re.finditer(r"(?<![\w])ký kết (?:quy chế|chương trình|kế hoạch) phối hợp|ký kết thỏa thuận hợp tác", s):
        os_ = [m for m in args(ms, (O,)) if m.end <= t.start() and t.start() - m.end <= 120]
        if len(os_) >= 2 and re.fullmatch(r"\s*(?:và|với)\s*", s[os_[-2].end:os_[-1].start]):
            out.append({"rel": "PHOI_HOP", "src": os_[-2].id, "src_label": "Organization", "dst": os_[-1].id,
                        "dst_label": "Organization", "trigger": t.group(0), "conf": 0.9, "src_text": os_[-2].text,
                        "dst_text": os_[-1].text, "passive": False})
    return out


def main():
    lk = Linker()
    wiki_pos = set()
    for r in csv.DictReader((PROC / "edges_wiki.csv").open(encoding="utf-8")):
        if r["rel"] == "GIU_CHUC_VU":
            wiki_pos.add((r["src"], r["dst"]))
    mentions_out = (INTERIM / "relation_mentions.jsonl").open("w", encoding="utf-8")
    agg = {}
    n_docs = n_sents = 0
    ent_stats = Counter()
    for line in (INTERIM / "news_docs.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        n_docs += 1
        ctx = DocContext()
        for i, s in enumerate(d["sents"]):
            n_sents += 1
            ms = analyse_sentence(s, lk, ctx)
            for m in ms:
                ent_stats[(m.kind, m.via or "gaz")] += 1
            rels = extract_sentence(s, ms)
            # GIU_CHUC_VU từ cụm chức danh (chỉ khi Wikipedia chưa có cặp người–cơ quan này)
            for m in ms:
                if m.kind == P and m.via != "coref":
                    for role, oid in m.roles:
                        if (m.id, oid) in wiki_pos:
                            continue
                        rels.append({"rel": "GIU_CHUC_VU", "src": m.id, "src_label": "Person", "dst": oid,
                                     "dst_label": "Organization", "trigger": "appositive", "conf": round(min(m.conf, 0.9), 2),
                                     "src_text": m.text, "dst_text": lk.org_name.get(oid) or lk.new_orgs.get(oid, {}).get("name", oid),
                                     "role": role, "former": role.startswith("nguyên"), "passive": False})
            for r in rels:
                r.update({"doc_id": d["doc_id"], "url": d["url"], "date": d["date"], "sent_idx": i, "sentence": s})
                mentions_out.write(json.dumps(r, ensure_ascii=False) + "\n")
                key = (r["src"], r["rel"], r["dst"], r.get("role", "") if r["rel"] == "GIU_CHUC_VU" else "")
                a = agg.get(key)
                if a is None:
                    agg[key] = a = {"src": r["src"], "src_label": r["src_label"], "rel": r["rel"], "dst": r["dst"],
                                    "dst_label": r["dst_label"], "role": key[3], "start": r["date"], "end": "",
                                    "current": "" if r["rel"] != "GIU_CHUC_VU" else str(not r.get("former")),
                                    "source": r["url"], "confidence": r["conf"], "weight": 0, "evidence": s[:500],
                                    "date": r["date"], "method": "rule:" + r["trigger"], "to_org": r.get("to_org", "")}
                a["weight"] += 1
                a["confidence"] = max(a["confidence"], r["conf"])
                if r["date"] and (not a["start"] or r["date"] < a["start"]):
                    a["start"] = r["date"]
                if r["date"] and r["date"] > (a["date"] or ""):
                    a["date"] = r["date"]
                if r.get("to_org") and not a["to_org"]:
                    a["to_org"] = r["to_org"]
    mentions_out.close()

    # nút mới
    def write(path, rows, fields):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    used = {a["src"] for a in agg.values()} | {a["dst"] for a in agg.values()}
    new_p = [p for pid, p in lk.new_persons.items() if pid in used]
    write(PROC / "nodes_person_news.csv", new_p, ["id", "name", "wiki_title", "wikidata", "birth_year", "hometown", "source"])
    new_o = [o for oid, o in lk.new_orgs.items() if oid in used or any(e[0] == oid for e in lk.new_org_edges)]
    keep_o = {o["id"] for o in new_o}
    write(PROC / "nodes_org_news.csv", new_o, ["id", "name", "type", "level", "province"])
    existing_prov = {r["id"] for r in csv.DictReader((PROC / "nodes_province.csv").open(encoding="utf-8"))}
    missing_prov = []
    for name, pid in lk.prov_id.items():
        if pid not in existing_prov and pid not in {m["id"] for m in missing_prov}:
            missing_prov.append({"id": pid, "name": name, "status": lk.prov_status[name], "valid_from": ""})
    write(PROC / "nodes_province_news.csv", missing_prov, ["id", "name", "status", "valid_from"])

    edges = list(agg.values())
    for src, rel, dst, dl in lk.new_org_edges:
        if src in keep_o:
            edges.append({"src": src, "src_label": "Organization", "rel": rel, "dst": dst, "dst_label": dl,
                          "source": "rule:org_name", "confidence": 1.0, "weight": 1, "method": "rule:org_name"})
    seen, uniq = set(), []
    for e in edges:
        k = (e["src"], e["rel"], e["dst"], e.get("role", ""))
        if k not in seen:
            seen.add(k); uniq.append(e)
    fields = ["src", "src_label", "rel", "dst", "dst_label", "role", "start", "end", "current", "source", "confidence",
              "weight", "evidence", "date", "method", "to_org"]
    write(PROC / "edges_news.csv", uniq, fields)

    # mẫu đánh giá: 20 cạnh / loại cho 10 loại tin tức (+ GIU_CHUC_VU từ tin tức)
    EVAL.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(42)
    by_rel = defaultdict(list)
    for e in agg.values():
        by_rel[e["rel"]].append(e)
    sample = []
    for rel, lst in sorted(by_rel.items()):
        for e in rnd.sample(lst, min(20, len(lst))):
            sample.append({**e, "src_name": name_of(lk, e["src"]), "dst_name": name_of(lk, e["dst"]), "label": ""})
    write(EVAL / "sample_to_label.csv", sample, ["rel", "src_name", "dst_name", "role", "evidence", "source", "date",
                                                  "confidence", "src", "dst", "label"])

    c = Counter(e["rel"] for e in uniq)
    print(f"{n_docs} bài, {n_sents} câu")
    print("thực thể:", dict(ent_stats))
    print(f"nút mới: {len(new_p)} người, {len(new_o)} cơ quan, {len(missing_prov)} tỉnh")
    print(f"cạnh tin tức: {len(uniq)}")
    for k, v in c.most_common():
        print(f"  {k:18s} {v}")


def name_of(lk: Linker, i: str) -> str:
    return (lk.per_name.get(i) or lk.new_persons.get(i, {}).get("name") or lk.org_name.get(i)
            or lk.new_orgs.get(i, {}).get("name") or i)


if __name__ == "__main__":
    main()
