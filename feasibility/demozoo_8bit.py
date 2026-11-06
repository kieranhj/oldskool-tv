"""Size the 8-bit slice of Demozoo and its overlap with Pouet. Usage: python demozoo_8bit.py dz.sqlite pouet8.jsonl"""
import sqlite3, sys, json, collections
from common import DEMOZOO_8BIT
sys.stdout.reconfigure(encoding="utf8")
db = sqlite3.connect(sys.argv[1]); q = lambda s, *a: db.execute(s, a).fetchall()
ids = ",".join(f"'{i}'" for i in DEMOZOO_8BIT)  # dump loads as text
print("production columns:", [r[1] for r in q("pragma table_info(productions_production)")])
db.executescript(f"""
create temp table p8 as select distinct p.id, p.title, p.supertype from productions_production p
  join productions_production_platforms pp on pp.production_id = p.id where pp.platform_id in ({ids});
create temp table yt as select production_id pid, parameter vid from productions_productionlink where link_class='YoutubeVideo';
create temp table pl as select production_id pid, parameter pouet from productions_productionlink where link_class='PouetProduction';
create temp table cs as select production_id pid, parameter csdb from productions_productionlink where link_class='CsdbRelease';
""")
print("8-bit productions by supertype:", q("select supertype, count(*) from p8 group by 1"))
print("8-bit 'production' supertype with YouTube:", q("select count(distinct p8.id) from p8 join yt on yt.pid=p8.id where supertype='production'"))
print("by platform (all productions / with YouTube):")
for r in q(f"""select pf.name, count(distinct p8.id), count(distinct yt.pid) from p8
   join productions_production_platforms pp on pp.production_id=p8.id and pp.platform_id in ({ids})
   join platforms_platform pf on pf.id=pp.platform_id left join yt on yt.pid=p8.id
   where supertype='production' group by 1 order by 2 desc"""): print(f"  {r[0]:42} {r[1]:7} {r[2]:6}")
print("types of 8-bit YouTube prods:", q("""select t.name, count(distinct p8.id) from p8 join yt on yt.pid=p8.id
   join productions_production_types x on x.production_id=p8.id join productions_productiontype t on t.id=x.productiontype_id
   where supertype='production' group by 1 order by 2 desc limit 15"""))
# overlap with Pouet YouTube set
pouet = {str(json.loads(l)["id"]): json.loads(l) for l in open(sys.argv[2], encoding="utf8")}
dz_yt = q("select p8.id, group_concat(distinct yt.vid), (select group_concat(pouet) from pl where pl.pid=p8.id) from p8 join yt on yt.pid=p8.id where supertype='production' group by p8.id")
dz_pouet_ids = set(); n_with_pouet = 0
for pid, vids, pous in dz_yt:
    if pous: n_with_pouet += 1; dz_pouet_ids.update(pous.split(","))
all_dz_pouet = {r[0] for r in q("select pouet from pl join p8 on p8.id=pl.pid")}
print("Demozoo 8-bit YouTube prods:", len(dz_yt), " of which linked to a Pouet prod:", n_with_pouet)
print("Pouet 8-bit YouTube prods:", len(pouet), " also on Demozoo:", len(set(pouet) & all_dz_pouet),
      " also have YouTube on Demozoo:", len(set(pouet) & dz_pouet_ids))
union = len(dz_yt) + len(set(pouet) - dz_pouet_ids)
print("Union (approx distinct prods with a YouTube video from either site):", union)
# signals on Demozoo side
ct = q("select id from django_content_type where app_label='productions' and model='production'")[0][0]
print("8-bit prods with Demozoo comments:", q(f"select count(distinct object_id), count(*) from comments_comment where content_type_id='{ct}' and object_id in (select id from p8)"))
print("8-bit YouTube prods with tags:", q(f"select count(distinct object_id) from taggit_taggeditem where content_type_id='{ct}' and object_id in (select pid from yt join p8 on p8.id=yt.pid)"))
print("top tags on 8-bit prods:", q(f"""select t.name, count(*) from taggit_taggeditem i join taggit_tag t on t.id=i.tag_id
   where content_type_id='{ct}' and object_id in (select id from p8) group by 1 order by 2 desc limit 60"""))
print("8-bit YouTube prods with a compo placing:", q("select count(distinct production_id) from parties_competitionplacing where production_id in (select pid from yt join p8 on p8.id=yt.pid)"))
print("8-bit prods with award nominations:", q("select count(distinct production_id) from awards_nomination where production_id in (select id from p8)"))
print("8-bit prods with in-browser emulator config:", q("select count(distinct production_id) from productions_emulatorconfig where production_id in (select id from p8)"))
print("8-bit YouTube prods with CSDb link:", q("select count(distinct cs.pid) from cs join yt on yt.pid=cs.pid join p8 on p8.id=cs.pid"))
print("8-bit prods with credits:", q("select count(distinct production_id) from productions_credit where production_id in (select pid from yt join p8 on p8.id=yt.pid)"))
print("notes non-empty among 8-bit YouTube prods:", q("select count(distinct p.id) from productions_production p join yt on yt.pid=p.id join p8 on p8.id=p.id where length(coalesce(p.notes,''))>20"))
