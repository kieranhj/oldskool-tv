"""Download the public dumps and load the Demozoo tables we use into SQLite.

    python pipeline/ingest.py            # fetch anything missing, rebuild data/work/demozoo.sqlite if needed
    python pipeline/ingest.py --refresh  # fetch the latest dumps even if older ones are present

Sources (no scraping, bulk dumps only):
  - Pouet weekly dump, latest, from the JSON feed at data.pouet.net
  - Pouet's first archived dump (2019-07-25), the baseline for "votes gained since"
  - Demozoo nightly pg_dump from data.demozoo.org
"""
import gzip, json, re, sqlite3, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, WORK = ROOT / "data" / "raw", ROOT / "data" / "work"
UA = {"User-Agent": "oldskool-tv-pipeline (https://github.com/kieranhj)"}
BASELINE = "20190725"

DEMOZOO_TABLES = {
    "productions_production", "productions_production_platforms", "productions_production_types",
    "productions_productiontype", "platforms_platform", "productions_productionlink",
    "parties_competition", "parties_competitionplacing", "parties_party", "productions_credit",
    "demoscene_nick", "demoscene_releaser", "productions_production_author_nicks",
    "taggit_tag", "taggit_taggeditem", "django_content_type", "comments_comment",
    "awards_event", "awards_category", "awards_nomination", "productions_emulatorconfig",
    "pouet_production", "productions_screenshot",
}


def fetch(url, dest):
    print("downloading", url)
    req = urllib.request.Request(url, headers=UA)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.replace(dest)


def pouet_dumps(refresh):
    feed = json.load(urllib.request.urlopen(urllib.request.Request("https://data.pouet.net/json.php", headers=UA)))["dumps"]
    for date in (max(feed), BASELINE):
        info = feed[date]["prods"]
        ext = ".json.gz" if info["filename"].endswith(".gz") else ".json.xz"
        dest = RAW / f"pouet-prods-{date}{ext}"
        if not dest.exists() and (refresh or date == BASELINE or not list(RAW.glob("pouet-prods-2*"))) :
            fetch(info["url"], dest)


BS = "\\"
_ESC = re.compile(re.escape(BS) + "(.)")
_MAP = {"t": "\t", "n": "\n", "r": "\r", BS: BS}


def _unescape(v):
    return None if v == BS + "N" else _ESC.sub(lambda m: _MAP.get(m.group(1), m.group(1)), v)


def load_demozoo(dump, out):
    """Parse the COPY blocks of a plain pg_dump. All columns load as TEXT."""
    tmp = out.with_suffix(".part")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    cur = None
    for line in gzip.open(dump, "rt", encoding="utf8"):
        if cur is None:
            if line.startswith("COPY public."):
                name = line.split()[1].split(".")[1]
                if name in DEMOZOO_TABLES:
                    cols = [c.strip().strip('"') for c in line[line.find("(") + 1:line.find(")")].split(",")]
                    db.execute(f"CREATE TABLE {name} ({', '.join(chr(34) + c + chr(34) for c in cols)})")
                    ins = f"INSERT INTO {name} VALUES ({','.join('?' * len(cols))})"
                    cur, batch = name, []
            continue
        if line.startswith(BS + "."):
            db.executemany(ins, batch)
            print(f"  {cur}: {len(batch)} rows")
            cur = None
            continue
        batch.append([_unescape(v) for v in line.rstrip("\n").split("\t")])
    for idx in ("productions_productionlink(production_id)", "productions_productionlink(link_class, parameter)",
                "productions_production_platforms(production_id)", "productions_production_types(production_id)",
                "productions_credit(production_id)", "parties_competitionplacing(production_id)",
                "productions_production_author_nicks(production_id)", "taggit_taggeditem(object_id)",
                "productions_screenshot(production_id)", "pouet_production(pouet_id)"):
        db.execute(f"CREATE INDEX IF NOT EXISTS ix_{abs(hash(idx))} ON {idx}")
    db.commit()
    db.close()
    tmp.replace(out)


def main():
    refresh = "--refresh" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    pouet_dumps(refresh)
    dz = RAW / "demozoo-export.sql.gz"
    if refresh or not dz.exists():
        fetch("https://data.demozoo.org/demozoo-export.sql.gz", dz)
    db = WORK / "demozoo.sqlite"
    if refresh or not db.exists() or db.stat().st_mtime < dz.stat().st_mtime:
        print("loading Demozoo tables")
        load_demozoo(dz, db)
    else:
        # make sure indexes exist on a database built by the feasibility loader
        con = sqlite3.connect(db)
        con.execute("CREATE INDEX IF NOT EXISTS ix_link_pid ON productions_productionlink(production_id)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_link_cls ON productions_productionlink(link_class, parameter)")
        for t in ("productions_production_platforms", "productions_production_types", "productions_credit",
                  "parties_competitionplacing", "productions_production_author_nicks", "productions_screenshot"):
            con.execute(f"CREATE INDEX IF NOT EXISTS ix_{t}_pid ON {t}(production_id)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_tag_obj ON taggit_taggeditem(object_id)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_pouet_pid ON pouet_production(pouet_id)")
        con.commit()
    print("ingest done")


if __name__ == "__main__":
    main()
