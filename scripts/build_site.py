#!/usr/bin/env python3
"""Build a single-file HTML browser for a knowledge vault.

Usage:
    python scripts/build_site.py <vault_path>

Scans the vault (products -> repos -> markdown entries), parses frontmatter,
and writes a fully self-contained index.html next to the data so it can be
opened directly from disk (file://), copied, or shared. No server needed.
"""

import html
import json
import re
import sys
from pathlib import Path

import yaml


def parse_entry(path: Path):
    """Return (frontmatter dict, body str) for a knowledge entry file."""
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                fm = {}
            if isinstance(fm, dict):
                return fm, parts[2].strip()
    return {}, content.strip()


def collect(vault: Path):
    """Walk the vault and return the nested data structure for the browser."""
    products = []
    for product_dir in sorted(p for p in vault.iterdir() if p.is_dir() and not p.name.startswith(".")):
        repos = []
        for repo_dir in sorted(d for d in product_dir.iterdir() if d.is_dir()):
            entries = []
            for f in sorted(repo_dir.glob("*.md")):
                if f.name == "INDEX.md":
                    continue
                fm, body = parse_entry(f)
                entries.append({
                    "filename": f.name,
                    "title": str(fm.get("title") or f.stem),
                    "type": str(fm.get("type") or ""),
                    "status": str(fm.get("status") or ""),
                    "date": str(fm.get("date") or ""),
                    "summary": str(fm.get("summary") or ""),
                    "tags": fm.get("tags") or [],
                    "confidence": str(fm.get("confidence") or ""),
                    "body": body,
                    "rel": f"{repo_dir.name}/{f.name}",
                })
            entries.sort(key=lambda e: e["date"], reverse=True)
            if entries:
                repos.append({"name": repo_dir.name, "entries": entries})
        if repos:
            products.append({"name": product_dir.name, "repos": repos})
    return products


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Knowledge Vault</title>
<style>
:root{--bg:#fafafa;--panel:#fff;--border:#e2e2e6;--text:#1c1c21;--muted:#6b6b76;--acc:#2f6fed;--code:#f2f2f5}
*{box-sizing:border-box}body{margin:0;font:14px/1.65 -apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--text);background:var(--bg)}
#wrap{display:flex;height:100vh}
#side{width:320px;min-width:260px;border-right:1px solid var(--border);background:var(--panel);display:flex;flex-direction:column}
#head{padding:14px 16px 10px;border-bottom:1px solid var(--border)}
#head h1{margin:0 0 8px;font-size:16px}
#q{width:100%;padding:7px 10px;border:1px solid var(--border);border-radius:8px;font-size:13px;outline:none}
#q:focus{border-color:var(--acc)}
#filters{display:flex;gap:8px;padding:10px 16px;border-bottom:1px solid var(--border)}
#filters select{flex:1;padding:5px 6px;border:1px solid var(--border);border-radius:6px;font-size:12px;background:#fff}
#tree{flex:1;overflow-y:auto;padding:6px 8px 20px}
.prod{margin-top:10px;font-weight:700;font-size:13px;color:var(--muted);padding:2px 8px}
.repo{margin:4px 0 2px;font-size:12px;color:var(--muted);padding:2px 8px;font-family:ui-monospace,Consolas,monospace}
.ent{display:block;width:100%;text-align:left;padding:6px 8px 6px 16px;border:0;background:none;font-size:13px;color:var(--text);cursor:pointer;border-radius:6px;line-height:1.4}
.ent:hover{background:#eef3fe}
.ent.active{background:#e3edfd;font-weight:600}
.ent .d{color:var(--muted);font-size:11px;margin-right:6px}
.ent.hide{display:none}
#main{flex:1;overflow-y:auto;padding:28px 40px 80px;max-width:980px}
.badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px}
.b{font-size:11px;padding:2px 9px;border-radius:999px;border:1px solid var(--border);color:var(--muted);background:#fff}
.b.type{border-color:#c7d8fb;color:#2456c4;background:#eef3fe}
.b.status{border-color:#cdeacd;color:#2c7a2c;background:#eef9ee}
.b.status.superseded{border-color:#ecd2c7;color:#a2542c;background:#fdf3ee}
.b.status.proposed{border-color:#e6d8f5;color:#7443b8;background:#f7f1fd}
.b.conf{border-color:#f2e3b8;color:#8a6d1a;background:#fdf8e9}
h1.title{margin:2px 0 4px;font-size:24px;line-height:1.3}
.meta{color:var(--muted);font-size:12px;margin-bottom:18px}
.md{font-size:14.5px}
.md h1,.md h2,.md h3{margin:22px 0 8px;line-height:1.35}
.md h1{font-size:20px}.md h2{font-size:17px;padding-bottom:4px;border-bottom:1px solid var(--border)}.md h3{font-size:15px}
.md code{background:var(--code);border-radius:4px;padding:1px 5px;font-size:13px;font-family:ui-monospace,Consolas,monospace}
.md pre{background:var(--code);border:1px solid var(--border);border-radius:8px;padding:12px 14px;overflow-x:auto}
.md pre code{background:none;padding:0}
.md table{border-collapse:collapse;margin:12px 0;font-size:13px}
.md th,.md td{border:1px solid var(--border);padding:5px 12px;text-align:left}
.md th{background:var(--code)}
.md blockquote{margin:10px 0;padding:4px 14px;border-left:3px solid var(--acc);color:var(--muted);background:#f4f7fe}
.md a{color:var(--acc);text-decoration:none;border-bottom:1px dotted var(--acc)}
.md ul,.md ol{padding-left:24px}
#stats{font-size:11px;color:var(--muted);margin-top:6px}
#empty{color:var(--muted);text-align:center;margin-top:80px}
</style>
</head>
<body>
<div id="wrap">
  <nav id="side">
    <div id="head">
      <h1>Knowledge Vault</h1>
      <input id="q" placeholder="Search title / summary / body / tag...">
      <div id="stats"></div>
    </div>
    <div id="filters">
      <select id="ftype"><option value="">type: all</option></select>
      <select id="fstatus"><option value="">status: all</option></select>
    </div>
    <div id="tree"></div>
  </nav>
  <main id="main"><div id="empty">Select an entry from the left.</div></main>
</div>
<script>
const DATA = __DATA__;
const esc = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
const flat = [];
DATA.forEach(p => p.repos.forEach(r => r.entries.forEach(e => flat.push({...e, product: p.name, repo: r.name}))));

function inlineMd(s){
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\\*\\*([^*]+)\\*\\*/g, "<b>$1</b>");
  s = s.replace(/\\*([^*]+)\\*/g, "<i>$1</i>");
  s = s.replace(/\\[([^\\]]+)\\]\\(([^)]+\\.?[^)]*)\\)/g, (m, t, href) =>
    href.endsWith(".md") ? `<a href="#" data-jump="${href}">${t}</a>` : `<a href="${href}" target="_blank">${t}</a>`);
  return s;
}
function renderMd(src){
  const lines = src.split("\\n");
  let out = [], i = 0;
  while(i < lines.length){
    const L = lines[i];
    if(/^```/.test(L)){
      let j = i + 1, buf = [];
      while(j < lines.length && !/^```/.test(lines[j])){ buf.push(lines[j]); j++; }
      out.push("<pre><code>" + esc(buf.join("\\n")) + "</code></pre>");
      i = j + 1; continue;
    }
    if(/^\\s*\\|/.test(L) && i + 1 < lines.length && /^\\s*\\|[\\s:|-]+\\|?\\s*$/.test(lines[i+1])){
      const cells = row => row.trim().replace(/^\\||\\|$/g, "").split("|").map(c => c.trim());
      const head = cells(L); let j = i + 2, rows = [];
      while(j < lines.length && /^\\s*\\|/.test(lines[j])){ rows.push(cells(lines[j])); j++; }
      out.push("<table><tr>" + head.map(h => "<th>" + inlineMd(h) + "</th>").join("") + "</tr>" +
        rows.map(r => "<tr>" + r.map(c => "<td>" + inlineMd(c) + "</td>").join("") + "</tr>").join("") + "</table>");
      i = j; continue;
    }
    const h = L.match(/^(#{1,4})\\s+(.*)/);
    if(h){ out.push(`<h${h[1].length}>` + inlineMd(h[2]) + `</h${h[1].length}>`); i++; continue; }
    if(/^\\s*[-*]\\s+/.test(L)){
      let items = [];
      while(i < lines.length && /^\\s*[-*]\\s+/.test(lines[i])){ items.push("<li>" + inlineMd(lines[i].replace(/^\\s*[-*]\\s+/, "")) + "</li>"); i++; }
      out.push("<ul>" + items.join("") + "</ul>"); continue;
    }
    if(/^\\s*\\d+\\.\\s+/.test(L)){
      let items = [];
      while(i < lines.length && /^\\s*\\d+\\.\\s+/.test(lines[i])){ items.push("<li>" + inlineMd(lines[i].replace(/^\\s*\\d+\\.\\s+/, "")) + "</li>"); i++; }
      out.push("<ol>" + items.join("") + "</ol>"); continue;
    }
    if(/^>\\s?/.test(L)){ out.push("<blockquote>" + inlineMd(L.replace(/^>\\s?/, "")) + "</blockquote>"); i++; continue; }
    if(L.trim() === ""){ i++; continue; }
    let buf = [L]; i++;
    while(i < lines.length && lines[i].trim() !== "" && !/^(#{1,4}\\s|```|\\s*\\||>\\s?|\\s*[-*]\\s+)/.test(lines[i])){ buf.push(lines[i]); i++; }
    out.push("<p>" + inlineMd(buf.join(" ")) + "</p>");
  }
  return out.join("\\n");
}
function badge(cls, text){ return `<span class="b ${cls}">${esc(text)}</span>`; }
function show(rel){
  const e = flat.find(x => x.rel === rel);
  if(!e) return;
  document.querySelectorAll(".ent").forEach(b => b.classList.toggle("active", b.dataset.rel === rel));
  const tags = (e.tags || []).map(t => `<span class="b">#${esc(t)}</span>`).join("");
  const conf = e.confidence ? badge("conf", "confidence: " + e.confidence) : "";
  document.getElementById("main").innerHTML =
    `<div class="badges">${e.type ? badge("type", e.type) : ""}${e.status ? badge("status", e.status) : ""}${conf}${tags}</div>` +
    `<h1 class="title">${esc(e.title)}</h1>` +
    `<div class="meta">${esc(e.product)} / ${esc(e.repo)} / ${esc(e.filename)}${e.date ? " · " + e.date : ""}</div>` +
    `<div class="md">${renderMd(e.body || "")}</div>`;
  document.getElementById("main").scrollTop = 0;
}
function renderTree(){
  const q = document.getElementById("q").value.toLowerCase();
  const ft = document.getElementById("ftype").value;
  const fs = document.getElementById("fstatus").value;
  let shown = 0;
  const tree = document.getElementById("tree");
  tree.innerHTML = "";
  DATA.forEach(p => {
    let pHtml = "";
    p.repos.forEach(r => {
      let rHtml = "";
      r.entries.forEach(e => {
        const hay = (e.title + " " + e.summary + " " + (e.tags || []).join(" ") + " " + (e.body || "")).toLowerCase();
        const ok = (!q || hay.includes(q)) && (!ft || e.type === ft) && (!fs || e.status === fs);
        if(ok){ shown++; rHtml += `<button class="ent" data-rel="${e.rel}" onclick="show('${e.rel}')"><span class="d">${esc(e.date)}</span>${esc(e.title)}</button>`; }
      });
      if(rHtml){ pHtml += `<div class="repo">${esc(r.name)}</div>` + rHtml; }
    });
    if(pHtml){ tree.innerHTML += `<div class="prod">${esc(p.name)}</div>` + pHtml; }
  });
  if(!shown){ tree.innerHTML = '<div class="prod">No matches.</div>'; }
  document.getElementById("stats").textContent = shown + " / " + flat.length + " entries";
}
(function init(){
  const types = [...new Set(flat.map(e => e.type).filter(Boolean))].sort();
  const statuses = [...new Set(flat.map(e => e.status).filter(Boolean))].sort();
  const ft = document.getElementById("ftype"), fs = document.getElementById("fstatus");
  types.forEach(t => ft.add(new Option("type: " + t, t)));
  statuses.forEach(s => fs.add(new Option("status: " + s, s)));
  document.getElementById("q").addEventListener("input", renderTree);
  ft.addEventListener("change", renderTree);
  fs.addEventListener("change", renderTree);
  document.getElementById("main").addEventListener("click", ev => {
    const a = ev.target.closest("[data-jump]");
    if(a){ ev.preventDefault(); show(a.dataset.jump); }
  });
  renderTree();
  if(flat.length){ show(flat[0].rel); }
})();
</script>
</body>
</html>
"""


def build(vault: Path) -> Path:
    products = collect(vault)
    payload = json.dumps(products, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.replace("__DATA__", payload)
    out = vault / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


def main():
    if len(sys.argv) != 2:
        print("usage: python scripts/build_site.py <vault_path>", file=sys.stderr)
        sys.exit(2)
    vault = Path(sys.argv[1])
    if not vault.is_dir():
        print(f"error: {vault} is not a directory", file=sys.stderr)
        sys.exit(1)
    out = build(vault)
    n = sum(len(r["entries"]) for p in collect(vault) for r in p["repos"])
    print(f"built {out} ({n} entries)")


if __name__ == "__main__":
    main()
