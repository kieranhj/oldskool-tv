"""Size the 8-bit slice of the Pouet prods dump. Usage: python pouet_8bit.py prods.json.gz out.jsonl"""
import gzip, json, sys, collections
from common import POUET_8BIT, youtube_ids

prods = json.load(gzip.open(sys.argv[1]))["prods"]
out = open(sys.argv[2], "w", encoding="utf8")
n8 = 0; rows = []
plat = collections.Counter(); plat_yt = collections.Counter(); types = collections.Counter()
for p in prods:
    names = {pl["name"] for pl in (p.get("platforms") or {}).values()}
    if not names & POUET_8BIT:
        continue
    n8 += 1
    yts = [i for l in (p.get("downloadLinks") or []) for i in youtube_ids(l.get("link"))]
    for nm in names & POUET_8BIT:
        plat[nm] += 1
        if yts: plat_yt[nm] += 1
    if not yts:
        continue
    types.update(p.get("types") or [])
    r = dict(id=int(p["id"]), name=p["name"], types=p.get("types"), platforms=sorted(names),
             groups=[g["name"] for g in p.get("groups") or []], release=p.get("releaseDate"),
             up=int(p["voteup"] or 0), pig=int(p["votepig"] or 0), down=int(p["votedown"] or 0),
             cdc=int(p.get("cdc") or 0), popularity=float(p.get("popularity") or 0), rank=int(p.get("rank") or 0),
             placings=[(pl["party"]["name"], pl["year"], pl.get("compo_name"), pl["ranking"]) for pl in p.get("placings") or []],
             awards=p.get("awards"), demozoo=p.get("demozoo"), csdb=p.get("csdb"), zxdemo=p.get("zxdemo"),
             youtube=list(dict.fromkeys(yts)))
    rows.append(r); out.write(json.dumps(r) + "\n")

print("8-bit prods:", n8, " with YouTube:", len(rows))
print("per platform (all / with YouTube):")
for k, v in plat.most_common(): print(f"  {k:28} {v:6} {plat_yt[k]:6}")
print("types:", types.most_common(12))
votes = [r["up"] + r["pig"] + r["down"] for r in rows]
for t in (0, 1, 5, 10, 25, 50, 100):
    print(f"  YouTube prods with >= {t:3} votes: {sum(v >= t for v in votes)}")
print("  with cdc >= 1:", sum(r["cdc"] > 0 for r in rows), " with placing:", sum(bool(r["placings"]) for r in rows),
      " with award:", sum(bool(r["awards"]) for r in rows))
print("  multiple YouTube ids:", sum(len(r["youtube"]) > 1 for r in rows),
      " linked to demozoo:", sum(r["demozoo"] not in (None, "", "0") for r in rows),
      " linked to csdb:", sum(r["csdb"] not in (None, "", "0") for r in rows))
