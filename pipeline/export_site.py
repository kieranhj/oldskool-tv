"""Export the shortlist plus cards as the static site's data.

    python pipeline/export_site.py

Writes site/data/catalog.json (one record per video) and site/data/meta.json (counts, platforms, topics).
Prods without a card yet are exported with a plain factual fallback so the site always builds.
"""
import collections, datetime, json
from common import CACHE, CARDS, SITE_DATA, WORK, read_jsonl


POUET_KIND = {"demo": "Demo", "intro": "Intro", "cracktro": "Cracktro", "invitation": "Invitation",
              "dentro": "Intro"}


def kind(types):
    """One display label: a size class beats a plain 'Intro'; Pouet's lowercase types are mapped to Demozoo's."""
    norm = []
    for t in types:
        if t in POUET_KIND:
            norm.append(POUET_KIND[t])
        elif t[:-1].isdigit() and t[-1] in "kb":
            norm.append(t.upper().replace("B", "b") + " intro")  # 64k -> 64K intro, 256b -> 256b intro
        else:
            norm.append(t.replace(" Intro", " intro"))
    sized = [t for t in norm if t.endswith(" intro")]
    if sized:
        return sized[0]
    for t in ("Demo", "Invitation", "Cracktro", "Intro"):
        if t in norm:
            return t
    return norm[0] if norm else "Prod"


def fallback_card(c):
    where = next((f"{p['rank']}. in the {p['compo']} compo at {p['party']}" for p in c["placings"]
                  if str(p["rank"]).isdigit()), None)
    by = ", ".join(c["authors"]) or "unknown authors"
    return dict(summary=f"{kind(c['types'])} for the {c['family']} by {by}" + (f", {c['year']}" if c["year"] else "")
                + (f"; {where}." if where else "."), why="", highlights=[], topics=[], quote=None, basis="none")


def main():
    oembed = json.loads((CACHE / "oembed.json").read_text(encoding="utf8"))
    cards = {c["id"]: c for c in read_jsonl(CARDS / "cards.jsonl")} if (CARDS / "cards.jsonl").exists() else {}
    out = []
    for c in read_jsonl(WORK / "catalog.jsonl"):
        if not c["shortlist"]:
            continue
        vid = next(v for v in c["videos"] if oembed.get(v, {}).get("ok"))
        card = cards.get(c["id"]) or fallback_card(c)
        v = c["votes"]
        credits = collections.OrderedDict()
        for cr in c["credits"]:
            credits.setdefault(cr["category"], [])
            if cr["nick"] not in credits[cr["category"]]:
                credits[cr["category"]].append(cr["nick"])
        best = sorted((p for p in c["placings"] if str(p["rank"]).isdigit()), key=lambda p: int(p["rank"]))
        out.append(dict(
            id=c["id"], title=c["title"], by=c["authors"], year=c["year"], release=c["release"],
            platform=c["family"], kind=kind(c["types"]),
            video=vid, channel=oembed[vid].get("channel"),
            score=c["score"],
            votes=dict(up=v["up"], pig=v["pig"], down=v["down"], cdc=v["cdc"],
                       since2019=(v["up"] - v["up_2019"]) if c["year"] and c["year"] < 2019 else None),
            placings=[dict(rank=int(p["rank"]), compo=p["compo"], party=p["party"], year=p["year"]) for p in best[:3]],
            awards=[a for a in c["awards"]],
            credits=[dict(role=k, who=w) for k, w in credits.items()],
            links=dict(pouet=c["pouet"], demozoo=c["demozoo"], csdb=c["csdb"], zxart=c["zxart"]),
            emulator=bool(c["emulator"]),
            summary=card["summary"], why=card["why"], highlights=card["highlights"], topics=card["topics"],
            quote=card["quote"], basis=card["basis"],
        ))
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "catalog.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    meta = dict(
        generated=datetime.date.today().isoformat(), videos=len(out), cards=sum(r["basis"] != "none" for r in out),
        platforms=collections.Counter(r["platform"] for r in out).most_common(),
        topics=collections.Counter(t for r in out for t in r["topics"]).most_common(),
        years=[min(r["year"] for r in out if r["year"]), max(r["year"] for r in out if r["year"])],
    )
    (SITE_DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"exported {len(out)} videos ({meta['cards']} with cards) to {SITE_DATA}")


if __name__ == "__main__":
    main()
