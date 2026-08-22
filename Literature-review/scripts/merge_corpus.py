"""Merge every raw angle/expansion JSON from the sweep into one deduped corpus."""
import json, os, re, sys, glob, unicodedata
from collections import defaultdict

RAW = sys.argv[1] if len(sys.argv) > 1 else "corpus/raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "corpus/corpus.json"

def norm_title(t):
    t = unicodedata.normalize("NFKD", (t or "")).encode("ascii", "ignore").decode()
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def norm_id(p):
    for k in ("id", "url", "pdf_url"):
        v = p.get(k) or ""
        m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", v, re.I)
        if m: return "arxiv:" + m.group(1)
        m = re.search(r"^arxiv:\s*(\d{4}\.\d{4,5})", v, re.I)
        if m: return "arxiv:" + m.group(1)
        m = re.search(r"(10\.\d{4,9}/[^\s\"'<>]+)", v)
        if m: return "doi:" + m.group(1).lower().rstrip(".,;)")
    return None

records, files = [], sorted(glob.glob(os.path.join(RAW, "*.json")))
for f in files:
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print(f"  !! {os.path.basename(f)}: {e}"); continue
    papers = d.get("papers", d) if isinstance(d, dict) else d
    if not isinstance(papers, list): continue
    src = os.path.splitext(os.path.basename(f))[0]
    for p in papers:
        if isinstance(p, dict) and p.get("title"):
            p["_src"] = src
            records.append(p)
    print(f"  {os.path.basename(f):32s} {len(papers):4d} papers")

by_key, merged = {}, []
for p in records:
    k = norm_id(p) or ("t:" + norm_title(p["title"]))
    if k in by_key:
        e = by_key[k]
        e["_src"] = e["_src"] + "," + p["_src"]
        for fld in ("abstract", "pdf_url", "venue", "authors", "id", "relevance"):
            if not e.get(fld) and p.get(fld): e[fld] = p[fld]
        # keep the strongest tier
        rank = {"core": 3, "adjacent": 2, "background": 1}
        if rank.get(p.get("tier"), 0) > rank.get(e.get("tier"), 0): e["tier"] = p["tier"]
        e["citations"] = max(e.get("citations") or 0, p.get("citations") or 0)
    else:
        p["_key"] = k
        by_key[k] = p
        merged.append(p)

rank = {"core": 3, "adjacent": 2, "background": 1}
merged.sort(key=lambda p: (-rank.get(p.get("tier"), 0), -(p.get("citations") or 0), -(p.get("year") or 0)))
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
json.dump(merged, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

tiers = defaultdict(int); years = defaultdict(int)
for p in merged:
    tiers[p.get("tier", "?")] += 1; years[p.get("year", 0)] += 1
print(f"\nfiles={len(files)} raw={len(records)} unique={len(merged)}")
print("tiers:", dict(tiers))
print("years:", dict(sorted(years.items())))
print("->", OUT)
