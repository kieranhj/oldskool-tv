"""Fetch Pouet comments for a stratified sample of 8-bit YouTube prods, politely (1 request/second).
Usage: python pouet_comments_sample.py pouet8.jsonl out.jsonl [n_per_band]"""
import json, sys, time, random, urllib.request

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf8")]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
bands = [(0, 4), (5, 9), (10, 24), (25, 49), (50, 10**9)]
random.seed(8)
sample = []
for lo, hi in bands:
    b = [r for r in rows if lo <= r["up"] + r["pig"] + r["down"] <= hi]
    sample += [(f"{lo}-{hi}", r) for r in random.sample(b, min(n, len(b)))]
with open(sys.argv[2], "w", encoding="utf8") as out:
    for band, r in sample:
        req = urllib.request.Request(f"https://api.pouet.net/v1/prod/comments/?id={r['id']}",
                                     headers={"User-Agent": "oldskool-tv-feasibility (contact: khconnell@gmail.com)"})
        try:
            j = json.load(urllib.request.urlopen(req, timeout=30))
            cs = [dict(id=c["id"], user=c["user"]["nickname"], rating=int(c["rating"]), date=c["addedDate"],
                       text=c["comment"]) for c in j["prod"].get("comments") or []]
        except Exception as e:
            cs = None; print("error", r["id"], e, file=sys.stderr)
        out.write(json.dumps(dict(id=r["id"], band=band, votes=r["up"] + r["pig"] + r["down"], comments=cs)) + "\n")
        out.flush(); time.sleep(1)
