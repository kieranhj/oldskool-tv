"""Fetch a random sample of CSDb releases (those Demozoo links from 8-bit YouTube prods) at 1 request/second
and measure comments, rating and YouTube links. Usage: python csdb_sample.py dz.sqlite n out.jsonl"""
import sqlite3, sys, random, time, json, urllib.request, xml.etree.ElementTree as ET
from common import DEMOZOO_8BIT, youtube_ids
db = sqlite3.connect(sys.argv[1])
ids = ",".join(f"'{i}'" for i in DEMOZOO_8BIT)
rows = db.execute(f"""select distinct cs.parameter from productions_productionlink cs
  join productions_productionlink yt on yt.production_id=cs.production_id and yt.link_class='YoutubeVideo'
  join productions_production_platforms pp on pp.production_id=cs.production_id and pp.platform_id in ({ids})
  where cs.link_class='CsdbRelease'""").fetchall()
random.seed(64); sample = random.sample([r[0] for r in rows], int(sys.argv[2]))
with open(sys.argv[3], "w", encoding="utf8") as out:
    for rid in sample:
        req = urllib.request.Request(f"https://csdb.dk/webservice/?type=release&id={rid}",
                                     headers={"User-Agent": "oldskool-tv-feasibility (contact: khconnell@gmail.com)"})
        try:
            x = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
            rel = x.find("Release")
            comments = [dict(kind=c.tag, text=(c.findtext("Text") or "").strip(), date=c.findtext("Date"))
                        for grp in rel.findall("Comments") for c in grp]
            links = " ".join(l.text or "" for l in rel.iter("Link"))
            out.write(json.dumps(dict(id=rid, name=rel.findtext("Name"), type=rel.findtext("Type"), rating=rel.findtext("Rating"),
                                      comments=comments, youtube=youtube_ids(links))) + "\n")
        except Exception as e:
            print("error", rid, e, file=sys.stderr)
        time.sleep(1)
