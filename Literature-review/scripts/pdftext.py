"""Fetch a PDF (URL or local path) and dump its full text.
Usage: python pdftext.py <url_or_path> [outfile] [--sections]
"""
import sys, os, re, io, urllib.request, hashlib

def fetch(src):
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={
            "User-Agent": "Mozilla/5.0 (compatible; academic-research-bot/1.0)"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.read()
    return open(src, "rb").read()

def extract(data):
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    parts = []
    for i, page in enumerate(doc):
        parts.append(f"\n<<<PAGE {i+1}>>>\n" + page.get_text("text"))
    doc.close()
    return "".join(parts)

def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
    txt = extract(fetch(src))
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{4,}", "\n\n\n", txt)
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        open(out, "w", encoding="utf-8").write(txt)
        print(f"{len(txt)} chars -> {out}")
    else:
        sys.stdout.write(txt)

if __name__ == "__main__":
    main()
