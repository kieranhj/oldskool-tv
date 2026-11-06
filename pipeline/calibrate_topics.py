"""Topic calibration: pick a batch, fetch YouTube stills, build labelling inputs, and render a review page.

    python pipeline/calibrate_topics.py prepare   # pick ~30 prods, fetch 3 stills each, write fact sheets
    python pipeline/calibrate_topics.py report    # after labelling: write data/work/calibration/report.html

Stills are YouTube's own auto-generated frames (about 25/50/75% through the video), at the largest size
available: maxres1-3 (1280x720), then sd1-3 (640x480), then hq1-3 (480x360).
"""
import html, json, sys, time, urllib.error, urllib.request
from common import CACHE, WORK, UA, read_jsonl, write_jsonl

OUT = WORK / "calibration"
FRAMES = CACHE / "frames"
# Tags that map straight to a topic or badge (applied in code, and shown to the labeller)
TAG_RULES = {
    "petscii": "text-mode", "petscii-animations": "text-mode", "atascii": "text-mode", "textmode": "text-mode",
    "teletext": "text-mode",
    "bad-apple": "video", "stniccc-challenge": "video", "video-footage": "video",
    "plasma": "effects", "sierpinski": "effects", "raycasting": "effects", "rotozoomer": "effects",
    "tunnel": "effects", "twister": "effects", "rotating-raster": "effects", "border-scroll": "effects",
    "3d": "3d", "vectors": "3d", "glenz": "3d", "dot-ball": "3d",
    "pixel-art": "pixel-art", "slideshow": "pixel-art",
}
EXPANDED_TAGS = {"reu": "REU", "vbxe": "VBXE", "2sid": "2SID", "zx-spectrum-128k": "128K", "128k": "128K",
                 "zx-spectrum-next": "Spectrum Next", "msx2": "MSX2", "1mbit": "1Mbit cart", "bbc-master": "BBC Master",
                 "256k": "256K"}
# The calibration labels used the earlier, finer families; fold them into the six topics for the report
FOLD = {"filled-3d": "3d", "vectors": "3d", "rasters": "effects", "borders": "effects", "screen-modes": "effects",
        "sprites": "effects", "scrollers": "effects", "chunky-fx": "effects", "plasma-fractals": "effects",
        "size-coding": "tiny"}
TOPICS = ("3d", "effects", "pixel-art", "text-mode", "video", "tiny")


def fold(families):
    out = {}
    for f in families:
        t = FOLD.get(f["id"], f["id"])
        if t in TOPICS:
            o = out.setdefault(t, {"id": t, "evidence": [], "from": []})
            o["from"].append(f["id"])
            o["evidence"] += [x for x in f.get("evidence", []) if x not in o["evidence"]]
    return list(out.values())


def pick(catalog):
    sl = [c for c in catalog if c["shortlist"]]
    batch = [c for c in sl if c["family"] == "BBC Micro"]
    c64 = sorted((c for c in sl if c["family"] == "Commodore 64" and c["csdb"]), key=lambda c: -c["score"])
    batch += c64[:10]
    quota = {"ZX Spectrum": 4, "Atari 8-bit": 3, "Amstrad CPC": 3, "Atari VCS": 1, "C16/Plus 4": 1, "MSX": 1,
             "Game Boy": 1, "VIC-20": 1, "NES": 1}
    for fam, n in quota.items():
        batch += [c for c in sl if c["family"] == fam][:n]
    return batch


def fetch_frames(vid):
    got = []
    for n in (1, 2, 3):
        dest = FRAMES / f"{vid}_{n}.jpg"
        if not dest.exists():
            for size in ("maxres", "sd", "hq"):
                try:
                    data = urllib.request.urlopen(urllib.request.Request(
                        f"https://i.ytimg.com/vi/{vid}/{size}{n}.jpg", headers=UA), timeout=20).read()
                    dest.write_bytes(data)
                    break
                except urllib.error.HTTPError:
                    continue
            time.sleep(0.2)
        if dest.exists():
            got.append(str(dest))
    return got


def prepare():
    FRAMES.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = read_jsonl(WORK / "catalog.jsonl")
    oembed = json.loads((CACHE / "oembed.json").read_text(encoding="utf8"))
    sheets_by_id = {s["id"]: s for f in sorted((WORK / "card_inputs").glob("batch_*.jsonl")) for s in read_jsonl(f)}
    rows = []
    for c in pick(catalog):
        vid = next(v for v in c["videos"] if oembed.get(v, {}).get("ok"))
        s = dict(sheets_by_id[c["id"]])
        s["all_tags"] = c["tags"]
        s["tag_families"] = sorted({TAG_RULES[t] for t in c["tags"] if t in TAG_RULES})
        s["tag_expanded"] = sorted({EXPANDED_TAGS[t] for t in c["tags"] if t in EXPANDED_TAGS})
        s["video"] = vid
        s["frames"] = fetch_frames(vid)
        rows.append(s)
    for i, half in enumerate((rows[:len(rows) // 2], rows[len(rows) // 2:]), 1):
        write_jsonl(OUT / f"inputs_{i}.jsonl", half)
    print(f"{len(rows)} prods, {sum(len(r['frames']) for r in rows)} frames; inputs in {OUT}")
    for r in rows:
        print(f"  {r['id']:10} {r['platform']:14} {r['title'][:40]:40} frames {len(r['frames'])}  tags->{r['tag_families']}")


def report():
    sheets = {s["id"]: s for f in sorted(OUT.glob("inputs_*.jsonl")) for s in read_jsonl(f)}
    labels = [l for f in sorted(OUT.glob("labels_*.jsonl")) for l in read_jsonl(f)]
    names = {}
    for line in (WORK.parent.parent / "pipeline" / "TOPICS.md").read_text(encoding="utf8").splitlines():
        if line.startswith("| `"):
            cells = [x.strip() for x in line.strip("|").split("|")]
            names[cells[0].strip("`")] = cells[1]
    e = html.escape
    parts = []
    for l in labels:
        s = sheets[l["id"]]
        fams = "".join(
            f'<li>'
            f'<b>{e(names.get(f["id"], f["id"]))}</b> <span class="conf">{e(", ".join(f["from"]))}</span>'
            f'<br><small>{e("; ".join(f.get("evidence", [])))}</small></li>' for f in fold(l["families"]))
        frames = "".join(f'<figure><img loading="lazy" src="https://i.ytimg.com/vi/{s["video"]}/hq{n}.jpg" alt="frame {n}">'
                         f'<figcaption>{e(l.get("frame_notes", ["", "", ""])[n - 1] if len(l.get("frame_notes", [])) >= n else "")}</figcaption></figure>'
                         for n in (1, 2, 3))
        parts.append(f"""<section id="{e(l['id'])}">
  <h2>{e(s['title'])} <small>{e(', '.join(s['by']))} · {e(s['platform'])} · {e(str(s['released'])[:4])}</small></h2>
  <p class="lean">Expanded: {e(', '.join(l.get('expanded') or []) or 'stock')}
     · <a href="https://www.youtube.com/watch?v={s['video']}" target="_blank">video</a>
     · <a href="https://demozoo.org/productions/{s['id'][2:]}/" target="_blank">Demozoo</a></p>
  <div class="frames">{frames}</div>
  <ul class="fams">{fams}</ul>
  {f'<p class="notes">{e(l["notes"])}</p>' if l.get('notes') else ''}
  <p class="input">Tags: {e(', '.join(s['all_tags']) or 'none')} · CSDb comments: {len(s.get('csdb_comments', []))}</p>
</section>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Topic calibration</title><style>
body{{font:15px/1.45 system-ui,sans-serif;margin:0;padding:24px 16px;background:#111;color:#eee}} main{{max-width:1100px;margin:0 auto}}
a{{color:#7cc7ff}} h1{{margin:0 0 6px}} section{{border-top:1px solid #333;padding:18px 0}} h2{{margin:0 0 4px;font-size:19px}} h2 small{{color:#aaa;font-weight:400;font-size:14px}}
.frames{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}} figure{{margin:0}} img{{width:100%;border-radius:6px;display:block}}
figcaption{{font-size:12px;color:#aaa;margin-top:4px}} .fams{{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px}}
.fams li{{background:#1d1d22;border-left:4px solid #888;border-radius:6px;padding:6px 10px;max-width:340px}} .fams li.effect{{border-color:#57c4d8}} .fams li.content{{border-color:#888}}
.conf{{color:#aaa;font-size:12px}} small{{color:#aaa}} .notes,.input{{color:#aaa;font-size:13px}} .key span{{display:inline-block;padding:0 8px;border-left:4px solid;margin-right:10px}}
@media (max-width:640px){{.frames{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Topic calibration: {len(labels)} prods</h1>
<p>The stills are YouTube's three automatic frames.</p>
{''.join(parts)}
</main></body></html>"""
    (OUT / "report.html").write_text(page, encoding="utf8")
    print("wrote", OUT / "report.html")


if __name__ == "__main__":
    {"prepare": prepare, "report": report}[sys.argv[1]]()
