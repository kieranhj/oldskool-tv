"""First-cut 'classics' ranking for 8-bit prods, using only data available without comments:
Pouet votes now vs. July 2019 (from the archived dumps), coups de coeur, compo placings.
Usage: python rank_sketch.py pouet8.jsonl prods-2019.json.xz"""
import json, sys, lzma, math, collections
sys.stdout.reconfigure(encoding="utf8")
now = [json.loads(l) for l in open(sys.argv[1], encoding="utf8")]
old = {int(p["id"]): p for p in json.load(lzma.open(sys.argv[2]))["prods"]}
for r in now:
    o = old.get(r["id"])
    ov = (int(o["voteup"] or 0), int(o["votepig"] or 0), int(o["votedown"] or 0)) if o else (0, 0, 0)
    r["new_up"] = r["up"] - ov[0]; r["old_total"] = sum(ov)
    tot = r["up"] + r["pig"] + r["down"]
    # Wilson lower bound on thumbs-up share (pig counts as half), so a few votes can't top the chart
    pos = r["up"] + 0.5 * r["pig"]
    if tot:
        z = 1.64; ph = pos / tot
        r["wilson"] = (ph + z*z/(2*tot) - z*math.sqrt((ph*(1-ph) + z*z/(4*tot))/tot)) / (1 + z*z/tot)
    else:
        r["wilson"] = 0
    top3 = any(str(p[3]) in ("1", "2", "3") for p in r["placings"])
    r["score"] = r["wilson"] * math.log1p(r["up"]) + 0.5 * math.log1p(max(r["new_up"], 0)) + 0.5 * math.log1p(r["cdc"]) + (0.3 if top3 else 0)
pre = [r for r in now if r["release"] and r["release"][:4] < "2019"]
print("pre-2019 8-bit YouTube prods:", len(pre), " gaining >=1 thumb up since Jul 2019:", sum(r["new_up"] > 0 for r in pre),
      " >=5:", sum(r["new_up"] >= 5 for r in pre), " >=10:", sum(r["new_up"] >= 10 for r in pre))
def show(title, rows, n=25):
    print("\n" + title)
    for r in rows[:n]:
        print(f"  {r['score']:5.2f}  {r['name'][:34]:34} {', '.join(r['groups'])[:26]:26} {(r['release'] or '')[:4]:4} "
              f"{'/'.join(p[:12] for p in r['platforms'])[:22]:22} up {r['up']:3} (+{r['new_up']:3} since 2019) cdc {r['cdc']}")
rank = sorted(now, key=lambda r: -r["score"])
show("Top 25 overall", rank)
show("Pre-2000 classics still gaining votes since 2019", [r for r in sorted(pre, key=lambda r: -r["new_up"]) if r["release"][:4] < "2000"], 15)
by = collections.defaultdict(list)
for r in rank:
    for p in r["platforms"]: by[p].append(r)
for p in ("BBC Micro", "ZX Spectrum", "Atari XL/XE", "Amstrad CPC"):
    show(f"Top 5 {p}", by[p], 5)
