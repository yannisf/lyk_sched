#!/usr/bin/env python3
"""Download the PDF of the newest "ΠΡΟΓΡΑΜΜΑ" post on 22lyk-athin.att.sch.gr.

Saves it under pdfs/ (keeping the 5 newest) and points programma-latest.pdf at it. A rerun downloads
again only if the post now links a different PDF or the PDF itself changed.
Exit 0 = new or unchanged, 1 = failed (previous files are left untouched).
"""
import hashlib, html, http.client, json, os, re, sys, time, unicodedata
import urllib.error, urllib.parse, urllib.request
from datetime import datetime

SITE = os.environ.get("PROGRAMMA_SITE", "http://22lyk-athin.att.sch.gr")
TIMEOUT = float(os.environ.get("PROGRAMMA_TIMEOUT", 90))  # per attempt; the API can take 30s+
WAITS = (5, 15, 30)  # pause before each of the 3 retries
KEEP = int(os.environ.get("PROGRAMMA_KEEP", 5))  # newest PDFs kept in pdfs/
API = SITE + "/wp-json/wp/v2/posts?orderby=date&order=desc&per_page=20&_fields=id,title,content"

HERE = os.path.dirname(os.path.abspath(__file__))
LINK = os.path.join(HERE, "programma-latest.pdf")
STATE = os.path.join(HERE, ".state.json")

# Titles are typed on mixed keyboards: "Πρόγραμμα", "προγραμμα", "ΠPOΓPAMMA" (Latin P/O/A/M).
LATIN_TO_GREEK = str.maketrans("ABEHIKMNOPTXYZ", "ΑΒΕΗΙΚΜΝΟΡΤΧΥΖ")
# Whole word plus inflections, so "Προγραμματισμός" does not match.
TITLE_RE = re.compile(r"(?<!\w)ΠΡΟΓΡΑΜΜΑ(?:ΤΑ|ΤΟΣ|ΤΩΝ)?(?!\w)")
PDF_RE = re.compile(r'href="([^"]+?\.pdf)"', re.I)


class Fail(Exception):
    """A problem to report to the user; retrying won't help."""


class Retry(Exception):
    """A transient problem; worth another attempt."""


def describe(e):
    if isinstance(e, urllib.error.URLError) and not isinstance(e, urllib.error.HTTPError):
        e = e.reason
    if isinstance(e, TimeoutError):
        return f"timed out after {TIMEOUT:g}s"
    return str(e) or type(e).__name__


def fetch(url, headers=None, check=None):
    """GET url, retrying transient errors. Returns (status, headers, body).

    A 304 returns an empty body. check(body) may raise Retry for a bad 200
    (e.g. a proxy error page) and its return value replaces the body.
    """
    attempts = len(WAITS) + 1
    req = urllib.request.Request(url, headers={"User-Agent": "fetch_programma", **(headers or {})})
    for n in range(1, attempts + 1):
        try:
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    status, hdrs, body = r.status, r.headers, r.read()
            except urllib.error.HTTPError as e:
                if e.code == 304:
                    return 304, e.headers, b""
                if e.code >= 500 or e.code == 429:
                    raise Retry(f"HTTP {e.code}")
                raise Fail(f"HTTP {e.code} for {urllib.parse.unquote(url)}")
            if not body:
                raise Retry("empty response")
            return status, hdrs, check(body) if check else body
        except (Retry, OSError, http.client.HTTPException) as e:  # timeouts, resets, DNS, ...
            reason = describe(e)
            if n == attempts:
                host = urllib.parse.urlsplit(url).netloc
                raise Fail(f"{host} failed {attempts} times in a row ({reason})")
            print(f"attempt {n}/{attempts} failed ({reason}), retrying in {WAITS[n - 1]}s…", file=sys.stderr)
            time.sleep(WAITS[n - 1])


def parse_posts(body):
    try:
        posts = json.loads(body)
    except ValueError:
        raise Retry("response was not valid JSON")
    if not isinstance(posts, list):
        raise Retry("unexpected API response")
    return posts


def is_pdf(body):
    if not body.startswith(b"%PDF"):
        raise Retry("response is not a PDF")
    return body


def is_programma(title):
    t = unicodedata.normalize("NFD", title)
    t = "".join(c for c in t if not unicodedata.combining(c)).upper().translate(LATIN_TO_GREEK)
    return bool(TITLE_RE.search(t))


def pick(posts):
    """(title, pdf_url) of the newest matching post that links a PDF; others are skipped."""
    for p in posts:
        title = html.unescape(p["title"]["rendered"]).strip()
        if is_programma(title):
            m = PDF_RE.search(html.unescape(p["content"]["rendered"]))
            if m:
                return title, m.group(1)
    raise Fail(f"no ΠΡΟΓΡΑΜΜΑ post with a PDF among the latest {len(posts)} posts")


def canonical(href):
    """Absolute URL with the path percent-encoded once (hrefs may hold raw Greek)."""
    u = urllib.parse.urlsplit(urllib.parse.urljoin(SITE + "/", href))
    return u._replace(path=urllib.parse.quote(urllib.parse.unquote(u.path))).geturl()


def write_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    os.replace(path + ".tmp", path)


def relink(target):
    if os.path.islink(LINK) and os.readlink(LINK) == target:
        return
    tmp = LINK + ".tmp"
    if os.path.lexists(tmp):
        os.remove(tmp)
    os.symlink(target, tmp)
    os.replace(tmp, LINK)


def prune(current):
    """Delete all but the KEEP newest PDFs (names start with a timestamp); never the current one."""
    pdfs = os.path.join(HERE, "pdfs")
    names = sorted(n for n in os.listdir(pdfs) if n.endswith(".pdf"))
    for n in names[:-KEEP]:
        if os.path.join("pdfs", n) != current:
            os.remove(os.path.join(pdfs, n))


def main():
    _, _, posts = fetch(API, check=parse_posts)
    title, href = pick(posts)
    url = canonical(href)

    try:
        with open(STATE) as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    have = bool(state.get("file")) and os.path.exists(os.path.join(HERE, state["file"]))

    headers = {}
    if have and state.get("url") == url:
        if state.get("etag"):
            headers["If-None-Match"] = state["etag"]
        if state.get("last_modified"):
            headers["If-Modified-Since"] = state["last_modified"]
    status, hdrs, body = fetch(url, headers, check=is_pdf)

    new = False
    if status != 304:
        digest = hashlib.sha256(body).hexdigest()
        if not (have and digest == state.get("sha256")):  # same bytes re-uploaded: keep the file we have
            name = os.path.basename(urllib.parse.unquote(urllib.parse.urlsplit(url).path))
            rel = os.path.join("pdfs", f"{datetime.now():%Y-%m-%d_%H%M}_{name}")
            write_atomic(os.path.join(HERE, rel), body)
            state, new = {"file": rel, "sha256": digest}, True
        state.update(title=title, url=url, etag=hdrs.get("ETag"), last_modified=hdrs.get("Last-Modified"))
        write_atomic(STATE, json.dumps(state, ensure_ascii=False, indent=1).encode())

    relink(state["file"])
    if new:
        prune(state["file"])
    if new:
        print(f"NEW: {title} → {state['file']} ({len(body) // 1024} KB), linked as programma-latest.pdf")
    else:
        print(f"Unchanged: {title} (programma-latest.pdf is current)")


if __name__ == "__main__":
    try:
        main()
    except Fail as e:
        sys.exit(f"ERROR: {e}. programma-latest.pdf left as it was.")
    except KeyboardInterrupt:
        sys.exit("Interrupted. programma-latest.pdf left as it was.")
    except Exception as e:
        sys.exit(f"ERROR: unexpected {type(e).__name__}: {e}. programma-latest.pdf left as it was.")
