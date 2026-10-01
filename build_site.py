#!/usr/bin/env python3
"""Build the GitHub Pages site in _site/: the kept PDFs, a copy of the latest
as programma-latest.pdf (Pages may not follow symlinks), and an index.html."""
import html, json, os, shutil, urllib.parse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "_site")

with open(os.path.join(HERE, ".state.json")) as f:
    state = json.load(f)

shutil.rmtree(SITE, ignore_errors=True)
shutil.copytree(os.path.join(HERE, "pdfs"), os.path.join(SITE, "pdfs"))
shutil.copy(os.path.join(HERE, state["file"]), os.path.join(SITE, "programma-latest.pdf"))

items = []
for n in sorted(os.listdir(os.path.join(SITE, "pdfs")), reverse=True):
    if n.endswith(".pdf"):
        items.append(f'<li><a href="pdfs/{urllib.parse.quote(n)}">{html.escape(n)}</a></li>')
now = datetime.now()  # local time; the workflow sets TZ=Europe/Athens

page = f"""<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Πρόγραμμα 22ου Λυκείου</title>
<style>
  :root {{ --bg: #fff; --fg: #1a1a1a; --muted: #666; --accent: #0b5cad; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #121212; --fg: #e8e8e8; --muted: #999; --accent: #6cb4ff; }} }}
  body {{ background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, sans-serif;
         max-width: 40rem; margin: 0 auto; padding: 1.5rem 1rem; }}
  a {{ color: var(--accent); }}
  .latest {{ display: inline-block; font-size: 1.25rem; font-weight: 600; margin: .5rem 0 1.5rem; }}
  li {{ margin: .3rem 0; word-break: break-word; }}
  small {{ color: var(--muted); }}
</style>
</head>
<body>
<h1>Πρόγραμμα 22ου ΓΕΛ Αθηνών</h1>
<a class="latest" href="programma-latest.pdf">📄 {html.escape(state.get("title", "Τελευταίο πρόγραμμα"))}</a>
<h2>Προηγούμενα</h2>
<ul>
{chr(10).join(items)}
</ul>
<p><small>Τελευταία ενημέρωση: {now:%d/%m/%Y %H:%M}, από το
<a href="http://22lyk-athin.att.sch.gr">22lyk-athin.att.sch.gr</a>.</small></p>
</body>
</html>
"""
with open(os.path.join(SITE, "index.html"), "w") as f:
    f.write(page)
print(f"Built {SITE} with {len(items)} PDF(s)")
