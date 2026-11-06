"""Load selected tables from the Demozoo nightly pg_dump (plain SQL, COPY blocks) into SQLite.
Usage: python demozoo_load.py demozoo-export.sql.gz out.sqlite"""
import gzip, sqlite3, sys, re

TABLES = {
    "productions_production", "productions_production_platforms", "productions_production_types",
    "productions_productiontype", "platforms_platform", "productions_productionlink",
    "parties_competition", "parties_competitionplacing", "parties_party", "productions_credit",
    "demoscene_nick", "demoscene_releaser", "productions_production_author_nicks",
    "taggit_tag", "taggit_taggeditem", "django_content_type", "comments_comment",
    "awards_event", "awards_category", "awards_nomination", "productions_emulatorconfig",
    "pouet_production", "productions_screenshot",
}

BS = "\\"
ESC = re.compile(re.escape(BS) + "(.)")
MAP = {"t": "\t", "n": "\n", "r": "\r", BS: BS}


def unescape(v):
    if v == BS + "N":
        return None
    return ESC.sub(lambda m: MAP.get(m.group(1), m.group(1)), v)


db = sqlite3.connect(sys.argv[2])
cur = None
for line in gzip.open(sys.argv[1], "rt", encoding="utf8"):
    if cur is None:
        if line.startswith("COPY public."):
            name = line.split()[1].split(".")[1]
            if name in TABLES:
                cols = [c.strip().strip('"') for c in line[line.find("(") + 1:line.find(")")].split(",")]
                db.execute(f"DROP TABLE IF EXISTS {name}")
                db.execute(f"CREATE TABLE {name} ({', '.join(chr(34) + c + chr(34) for c in cols)})")
                ins = f"INSERT INTO {name} VALUES ({','.join('?' * len(cols))})"
                cur, batch = name, []
        continue
    if line.startswith(BS + "."):
        db.executemany(ins, batch)
        db.commit()
        print(cur, len(batch))
        cur = None
        continue
    batch.append([unescape(v) for v in line.rstrip("\n").split("\t")])
db.close()
