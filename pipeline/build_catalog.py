"""Merge Pouet and Demozoo into one catalogue of 8-bit prods with a YouTube video, score them, and pick a shortlist.

    python pipeline/build_catalog.py [--size 300]

Writes data/work/catalog.jsonl: every candidate, scored, with "shortlist": true on the chosen ones.
"""
import argparse, collections, gzip, json, lzma, math, sqlite3
from common import (WORK, RAW, CACHE,DEMOZOO_8BIT, POUET_8BIT, POUET_FAMILY, WATCH_TYPES_POUET, family, watchable_dz,
                    youtube_ids, write_jsonl)

PRODUCTION_CT = None  # django content type id for productions.production, looked up at runtime


def load_pouet():
    dumps = sorted(p for p in RAW.glob("pouet-prods-*") if "20190725" not in p.name)
    latest = dumps[-1]
    opener = gzip.open if latest.suffix == ".gz" else lzma.open
    now = {int(p["id"]): p for p in json.load(opener(latest))["prods"]}
    base = {int(p["id"]): p for p in json.load(lzma.open(RAW / "pouet-prods-20190725.json.xz"))["prods"]}
    print(f"pouet: {len(now)} prods in {latest.name}, {len(base)} in the 2019 baseline")
    return now, base


def pouet_youtube(p):
    return [i for l in (p.get("downloadLinks") or []) for i in youtube_ids(l.get("link"))]


def pouet_is_8bit(p):
    return any(pl["name"] in POUET_8BIT for pl in (p.get("platforms") or {}).values())


def demozoo_rows(db):
    q = lambda s, *a: db.execute(s, a).fetchall()
    ids = ",".join(f"'{i}'" for i in DEMOZOO_8BIT)  # the dump loads every column as text
    ct = q("select id from django_content_type where app_label='productions' and model='production'")[0][0]
    prods = {r[0]: dict(dz=int(r[0]), title=r[1], notes=r[2] or "", release=r[3], release_precision=r[4])
             for r in q(f"""select distinct p.id, p.title, p.notes, p.release_date_date, p.release_date_precision
                 from productions_production p join productions_production_platforms pp on pp.production_id=p.id
                 where pp.platform_id in ({ids}) and p.supertype='production'""")}
    print(f"demozoo: {len(prods)} 8-bit productions")
    many = collections.defaultdict(list)

    def attach(key, sql):
        for pid, *vals in q(sql):
            if pid in prods:
                many[(pid, key)].append(vals[0] if len(vals) == 1 else vals)

    attach("platforms", """select pp.production_id, pf.name from productions_production_platforms pp
        join platforms_platform pf on pf.id=pp.platform_id""")
    attach("types", """select x.production_id, t.name from productions_production_types x
        join productions_productiontype t on t.id=x.productiontype_id""")
    attach("authors", """select a.production_id, n.name from productions_production_author_nicks a
        join demoscene_nick n on n.id=a.nick_id""")
    attach("credits", """select c.production_id, n.name, c.category, c.role from productions_credit c
        join demoscene_nick n on n.id=c.nick_id""")
    attach("youtube", "select production_id, parameter from productions_productionlink where link_class='YoutubeVideo'")
    attach("pouet", "select production_id, parameter from productions_productionlink where link_class='PouetProduction'")
    attach("csdb", "select production_id, parameter from productions_productionlink where link_class='CsdbRelease'")
    attach("zxart", "select production_id, parameter from productions_productionlink where link_class='ZxArtProduction'")
    attach("placings", """select cp.production_id, pa.name, substr(pa.start_date_date,1,4), c.name, cp.ranking
        from parties_competitionplacing cp join parties_competition c on c.id=cp.competition_id
        join parties_party pa on pa.id=c.party_id""")
    attach("awards", """select n.production_id, e.name, c.name, n.status from awards_nomination n
        join awards_category c on c.id=n.category_id join awards_event e on e.id=c.event_id""")
    attach("tags", f"""select i.object_id, t.name from taggit_taggeditem i join taggit_tag t on t.id=i.tag_id
        where i.content_type_id='{ct}'""")
    attach("screenshot", "select production_id, standard_url from productions_screenshot where standard_url<>''")
    attach("emulator", "select production_id, emulator, launch_url from productions_emulatorconfig")
    for (pid, key), vals in many.items():
        prods[pid][key] = vals
    return prods


def wilson(up, pig, down, z=1.64):
    n = up + pig + down
    if not n:
        return 0.0
    ph = (up + 0.5 * pig) / n
    return (ph + z * z / (2 * n) - z * math.sqrt((ph * (1 - ph) + z * z / (4 * n)) / n)) / (1 + z * z / n)


def score(c):
    v = c["votes"]
    s = wilson(v["up"], v["pig"], v["down"]) * math.log1p(v["up"])
    # "Still loved": thumbs gained since July 2019, only for prods that already existed then,
    # so recent releases aren't rewarded just for being recent.
    if c["year"] and c["year"] < 2019:
        s += 0.6 * math.log1p(max(v["up"] - v["up_2019"], 0))
    s += 0.5 * math.log1p(v["cdc"])
    best = min((int(p["rank"]) for p in c["placings"] if str(p["rank"]).isdigit()), default=None)
    s += {1: 0.4, 2: 0.25, 3: 0.25}.get(best, 0)
    if any(a["status"] == "winner" for a in c["awards"]):
        s += 0.4
    elif c["awards"]:
        s += 0.2
    return round(s, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=300)
    args = ap.parse_args()

    pouet, base = load_pouet()
    dz = demozoo_rows(sqlite3.connect(WORK / "demozoo.sqlite"))

    cands, seen_pouet = [], set()
    for d in dz.values():
        if not any(watchable_dz(t) for t in d.get("types", [])):
            continue
        pids = [int(x) for x in d.get("pouet", []) if x.isdigit() and int(x) in pouet]
        p = pouet[pids[0]] if pids else None
        seen_pouet.update(pids)
        yt_dz = list(dict.fromkeys(d.get("youtube", [])))
        yt_p = list(dict.fromkeys(pouet_youtube(p))) if p else []
        if not (yt_dz or yt_p):
            continue
        cands.append(merge(d, p, base, yt_dz, yt_p))
    # Pouet prods Demozoo doesn't know about (or doesn't link)
    for pid, p in pouet.items():
        if pid in seen_pouet or not pouet_is_8bit(p) or not set(p.get("types") or []) & WATCH_TYPES_POUET:
            continue
        if p.get("demozoo") and p["demozoo"].isdigit() and p["demozoo"] in dz:
            continue  # Demozoo has it but was filtered above (type or no video)
        yt_p = list(dict.fromkeys(pouet_youtube(p)))
        if yt_p:
            cands.append(merge(None, p, base, [], yt_p))

    for c in cands:
        c["score"] = score(c)
    pick_shortlist(cands, args.size)
    cands.sort(key=lambda c: -c["score"])
    write_jsonl(WORK / "catalog.jsonl", cands)
    sl = [c for c in cands if c["shortlist"]]
    print(f"{len(cands)} candidates, {len(sl)} shortlisted")
    for fam, n in collections.Counter(c["family"] for c in sl).most_common():
        print(f"  {fam:22} {n}")


def merge(d, p, base, yt_dz, yt_p):
    both = [v for v in yt_dz if v in yt_p]
    videos = list(dict.fromkeys(both + yt_dz + yt_p))
    if d:
        plats = sorted(set(d.get("platforms", [])))
        fams = sorted({family(x) for x in plats})
        # a multi-platform prod browses under its best-known 8-bit family
        fam = fams[0] if len(fams) == 1 else next((f for f in fams if f in POUET_FAMILY.values()), fams[0])
    else:
        plats = sorted(POUET_FAMILY.get(pl["name"], pl["name"]) for pl in p["platforms"].values()
                       if pl["name"] in POUET_8BIT)
        fam = plats[0]
    release = (d and d.get("release")) or (p and p.get("releaseDate")) or None
    if release and release.startswith("0000"):
        release = None
    year = int(release[:4]) if release else None
    pb = base.get(int(p["id"])) if p else None
    votes = dict(up=int(p["voteup"] or 0) if p else 0, pig=int(p["votepig"] or 0) if p else 0,
                 down=int(p["votedown"] or 0) if p else 0, cdc=int(p.get("cdc") or 0) if p else 0,
                 up_2019=int(pb["voteup"] or 0) if pb else 0)
    if d:
        placings = [dict(party=a, year=b, compo=c, rank=r) for a, b, c, r in d.get("placings", [])]
    else:
        placings = [dict(party=x["party"]["name"], year=x["year"], compo=x.get("compo_name"), rank=x["ranking"])
                    for x in p.get("placings") or []]
    authors = (d.get("authors") if d else None) or ([g["name"] for g in p.get("groups") or []] if p else [])
    return dict(
        id=f"dz{d['dz']}" if d else f"p{p['id']}",
        title=d["title"] if d else p["name"],
        authors=authors,
        release=release, year=year,
        platforms=plats, family=fam,
        types=sorted(set(d.get("types", []))) if d else p.get("types"),
        demozoo=d["dz"] if d else None,
        pouet=int(p["id"]) if p else None,
        csdb=(d.get("csdb") or [None])[0] if d else (p.get("csdb") if p and p.get("csdb") not in ("0", "") else None),
        zxart=(d.get("zxart") or [None])[0] if d else None,
        votes=votes,
        placings=placings,
        awards=[dict(event=e, category=c, status=s) for e, c, s in (d.get("awards", []) if d else [])],
        tags=sorted(set(d.get("tags", []))) if d else [],
        credits=[dict(nick=n, category=c, role=r) for n, c, r in (d.get("credits", []) if d else [])],
        notes=(d["notes"] if d else "")[:2000],
        screenshot=(d.get("screenshot") or [None])[0] if d else (p.get("screenshot") if p else None),
        emulator=[dict(emulator=e, url=u) for e, u in d.get("emulator", [])] if d else [],
        videos=videos,
    )


def pick_shortlist(cands, size):
    """Platform quotas proportional to sqrt(size of platform), so the C64 can't take every slot,
    then fill the rest by score. Only prods with some evidence (5+ Pouet votes, or a top-3 placing) qualify."""
    oembed = CACHE / "oembed.json"
    seen = json.loads(oembed.read_text(encoding="utf8")) if oembed.exists() else {}

    def eligible(c):
        if c["videos"] and all(v in seen and not seen[v]["ok"] for v in c["videos"]):
            return False  # every video known dead (run check_videos.py, then rebuild, to refill)
        v = c["votes"]
        top3 = any(str(p["rank"]) in ("1", "2", "3") for p in c["placings"])
        return v["up"] + v["pig"] + v["down"] >= 5 or top3
    by = collections.defaultdict(list)
    for c in sorted(cands, key=lambda c: -c["score"]):
        c["shortlist"] = False
        if eligible(c):
            by[c["family"]].append(c)
    # Quotas only reserve places for prods that are strong in absolute terms, so a tiny platform's best
    # effort doesn't take a slot just for existing; it can still win one on score in the fill.
    QUOTA_MIN_SCORE = 2.5
    weights = {f: math.sqrt(len(cs)) for f, cs in by.items()}
    total = sum(weights.values())
    chosen = []
    for f, cs in by.items():
        q = max(1, round(size * 0.8 * weights[f] / total))
        chosen += [c for c in cs[:q] if c["score"] >= QUOTA_MIN_SCORE]
    rest = sorted((c for cs in by.values() for c in cs if c not in chosen), key=lambda c: -c["score"])
    chosen += rest[:max(0, size - len(chosen))]
    for c in chosen[:size]:
        c["shortlist"] = True


if __name__ == "__main__":
    main()
