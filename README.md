# lyk_sched

Every hour from 14:00 to 22:00 (Athens time), a GitHub Action checks
[22lyk-athin.att.sch.gr](http://22lyk-athin.att.sch.gr) for the newest post whose title
contains "ΠΡΟΓΡΑΜΜΑ" (any case, with or without accents) and downloads its PDF if it is
new or has changed. The 5 most recent PDFs are kept and published with GitHub Pages:

- **Latest:** `https://lyk.frlab.eu/programma-latest.pdf`
- **List:** `https://lyk.frlab.eu/`

## Files

- `fetch_programma.py`: downloads the PDF, using only the Python standard library. It retries 3 times on errors and
  never re-downloads an unchanged PDF: the PDF request is conditional (ETag), and its
  contents are compared by SHA-256. Its state is kept in `.state.json`.
- `build_site.py`: builds the Pages site in `_site/`.
- `.github/workflows/fetch.yml`: the schedule. Use **Actions → Fetch programma → Run workflow**
  to run it now.

Run locally: `./fetch_programma.py` (it prints `NEW: …`, `Unchanged: …` or `ERROR: …`).
