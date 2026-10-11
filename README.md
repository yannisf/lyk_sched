# lyk_sched

`./update.sh`, run locally on demand, checks
[22lyk-athin.att.sch.gr](http://22lyk-athin.att.sch.gr) for the newest post whose title
contains "ΠΡΟΓΡΑΜΜΑ" (any case, with or without accents) and downloads its PDF if it is
new or has changed, then commits and pushes it. The push triggers a GitHub Action that
publishes the 5 most recent PDFs with GitHub Pages:

- **Latest:** <https://lyk.frlab.eu/programma-latest.pdf>
- **List:** <https://lyk.frlab.eu/>

## Files

- `update.sh`: pulls, runs `fetch_programma.py`, and commits and pushes any change
  (it prints `Nothing to push.` or `Pushed: …`).
- `fetch_programma.py`: downloads the PDF, using only the Python standard library. It retries 3 times on errors and
  never re-downloads an unchanged PDF: the PDF request is conditional (ETag), and its
  contents are compared by SHA-256. Its state is kept in `.state.json`.
- `build_site.py`: builds the Pages site in `_site/`.
- `.github/workflows/pages.yml`: builds and deploys the site on every push of new PDFs.
  To redeploy without one: `gh workflow run pages.yml -R yannisf/lyk_sched`.

`./fetch_programma.py` alone only downloads, without committing (it prints `NEW: …`,
`Unchanged: …` or `ERROR: …`).
