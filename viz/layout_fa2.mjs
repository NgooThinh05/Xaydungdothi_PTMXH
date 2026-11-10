// Tính lại bố cục cho viz/graph_data.js bằng ForceAtlas2 (Barnes-Hut, như Gephi).
// Khởi tạo từ bố cục Fruchterman–Reingold do build_view.py tính, rồi chạy FA2 để tách cụm.
//
//   cd viz && npm install --no-bin-links && node layout_fa2.mjs [số_vòng]
import fs from "node:fs";
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";

const FILE = new URL("./graph_data.js", import.meta.url);
const iterations = Number(process.argv[2] || 600);
const linLog = (process.argv[3] || "linlog") === "linlog";
const src = fs.readFileSync(FILE, "utf8");
const D = JSON.parse(src.slice(src.indexOf("{"), src.lastIndexOf("}") + 1));

const g = new Graph({ type: "undirected", multi: false });
for (const n of D.nodes) g.addNode(n.id, { x: n.x, y: n.y, size: 1 + Math.sqrt(n.d) });
for (const e of D.edges) {
  if (e.s === e.t) continue;
  if (g.hasEdge(e.s, e.t)) g.updateEdgeAttribute(e.s, e.t, "weight", w => w + 1);
  else g.addEdge(e.s, e.t, { weight: 1 });
}

const settings = {
  ...forceAtlas2.inferSettings(g),
  barnesHutOptimize: true,
  barnesHutTheta: 0.6,
  outboundAttractionDistribution: !linLog, // "dissuade hubs" khi không dùng LinLog
  linLogMode: linLog,                     // LinLog: tách cụm cộng đồng rõ hơn
  gravity: linLog ? 0.05 : 0.5,
  scalingRatio: linLog ? 2 : 8,
  slowDown: 3,
  edgeWeightInfluence: 0.5,
};
const t0 = Date.now();
forceAtlas2.assign(g, { iterations, settings, getEdgeWeight: "weight" });
console.log(`FA2 ${iterations} vòng: ${((Date.now() - t0) / 1000).toFixed(1)}s`);

for (const n of D.nodes) {
  const a = g.getNodeAttributes(n.id);
  n.x = Math.round(a.x * 100) / 100;
  n.y = Math.round(a.y * 100) / 100;
}
fs.writeFileSync(FILE, "window.GRAPH = " + JSON.stringify(D) + ";\n");
console.log("-> viz/graph_data.js");
