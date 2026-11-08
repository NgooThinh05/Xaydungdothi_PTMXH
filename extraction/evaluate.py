"""Tính độ chính xác (precision) của cạnh trích xuất từ tin tức trên mẫu đã gán nhãn thủ công.

Cách gán nhãn: mở data/eval/sample_to_label.csv, điền cột `label`:
  1 = đúng (quan hệ, chiều và cả hai thực thể đều đúng theo câu bằng chứng)
  0 = sai
  (để trống = bỏ qua)

    python extraction/evaluate.py [đường_dẫn_csv]
Kết quả in ra và ghi report/eval_precision.md
"""
from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - r) / d, (c + r) / d


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "eval" / "sample_to_label.csv"
    stats = defaultdict(lambda: [0, 0])
    for r in csv.DictReader(path.open(encoding="utf-8")):
        lab = (r.get("label") or "").strip()
        if lab not in ("0", "1"):
            continue
        stats[r["rel"]][0] += int(lab)
        stats[r["rel"]][1] += 1
    if not stats:
        print("Chưa có dòng nào được gán nhãn (cột label = 0/1).")
        return
    lines = ["| Quan hệ | Đúng / Đã gán | Precision | KTC 95% (Wilson) |", "|---|---|---|---|"]
    K = N = 0
    for rel in sorted(stats):
        k, n = stats[rel]
        K += k; N += n
        lo, hi = wilson(k, n)
        lines.append(f"| `{rel}` | {k} / {n} | {k / n:.1%} | {lo:.1%} – {hi:.1%} |")
    lo, hi = wilson(K, N)
    lines.append(f"| **Tổng** | **{K} / {N}** | **{K / N:.1%}** | {lo:.1%} – {hi:.1%} |")
    out = "\n".join(lines)
    print(out)
    (ROOT / "report").mkdir(exist_ok=True)
    (ROOT / "report" / "eval_precision.md").write_text(
        "# Độ chính xác cạnh trích xuất từ tin tức\n\nMẫu: " + str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        + "\n\n" + out + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
