"""Topic labels for the shortlist (see pipeline/TOPICS.md).

    python pipeline/label_topics.py prepare   # fetch 3 YouTube stills per prod, write data/work/topic_inputs/batch_NN.jsonl
    #   label each batch -> data/cards/topics_NN.jsonl
    python pipeline/label_topics.py check     # validate the labels and print counts

Tags that map straight to a topic, and "Tiny intros" (from the prod type), are applied in code on top of the
labeller's judgement, so the labeller can't miss them. export_site.py reads data/cards/topics_*.jsonl.
"""
import re, sys, time, urllib.error, urllib.request
from common import CACHE, CARDS, WORK, UA, read_jsonl, write_jsonl

TOPICS = {"3d": "3D & vectors", "effects": "2D effects", "pixel-art": "Pixel art", "text-mode": "Text-mode art",
          "tiny": "Tiny intros"}
TAG_RULES = {
    "petscii": "text-mode", "petscii-animations": "text-mode", "atascii": "text-mode", "textmode": "text-mode",
    "teletext": "text-mode",
    "plasma": "effects", "sierpinski": "effects", "raycasting": "effects", "rotozoomer": "effects",
    "tunnel": "effects", "twister": "effects", "rotating-raster": "effects", "border-scroll": "effects",
    "3d": "3d", "vectors": "3d", "glenz": "3d", "dot-ball": "3d",
    "pixel-art": "pixel-art", "slideshow": "pixel-art",
}
EXPANDED_TAGS = {"reu": "REU", "vbxe": "VBXE", "2sid": "2SID", "zx-spectrum-128k": "128K", "128k": "128K",
                 "zx-spectrum-next": "Spectrum Next", "msx2": "MSX2", "1mbit": "1Mbit cart", "bbc-master": "BBC Master",
                 "256k": "256K", "ts-conf": "TS-Conf", "requires-1mb": "1MB RAM",
                 "requires-16k-ram-expansion": "16K RAM expansion", "timex": "Timex"}
# One spelling per hardware requirement
HARDWARE_NAMES = {"C64-DTV": "C64 DTV", "Commodore 128": "C128", "ATM Turbo 2": "ATM Turbo", "CBM 8032": "PET 8032",
                  "PET 8296": "PET 8296", "ZX Spectrum Enhanced": "Enhanced Spectrum", "Expanded VRAM": "Expanded VRAM",
                  "AY": "AY sound chip"}
IN = WORK / "topic_inputs"
FRAMES = CACHE / "frames"
BATCH = 50


def tiny(types):
    """4K or smaller, from Demozoo ('4K Intro', '256b Intro') or Pouet ('4k', '256b') types."""
    for t in types:
        m = re.match(r"(\d+)\s*([kb])\b", t.lower())
        if m and (m.group(2) == "b" or int(m.group(1)) <= 4):
            return True
    return False


def fetch_frames(vid):
    """YouTube's three automatic stills (about 25/50/75% in); hq (480x360) is plenty for labelling."""
    got = []
    for n in (1, 2, 3):
        dest = FRAMES / f"{vid}_{n}.jpg"
        if not dest.exists():
            for size in ("hq", "sd", "maxres"):
                try:
                    dest.write_bytes(urllib.request.urlopen(urllib.request.Request(
                        f"https://i.ytimg.com/vi/{vid}/{size}{n}.jpg", headers=UA), timeout=20).read())
                    break
                except urllib.error.HTTPError:
                    continue
            time.sleep(0.2)
        if dest.exists():
            got.append(str(dest))
    return got


def prepare():
    import json
    FRAMES.mkdir(parents=True, exist_ok=True)
    IN.mkdir(parents=True, exist_ok=True)
    oembed = json.loads((CACHE / "oembed.json").read_text(encoding="utf8"))
    sheets = {s["id"]: s for f in sorted((WORK / "card_inputs").glob("batch_*.jsonl")) for s in read_jsonl(f)}
    cards = {c["id"]: c for c in read_jsonl(CARDS / "cards.jsonl")}
    rows = []
    for c in read_jsonl(WORK / "catalog.jsonl"):
        if not c["shortlist"]:
            continue
        vid = next(v for v in c["videos"] if oembed.get(v, {}).get("ok"))
        s = sheets.get(c["id"], {})
        card = cards.get(c["id"], {})
        rows.append(dict(
            id=c["id"], title=c["title"], by=c["authors"], platform=c["family"], types=c["types"],
            tags=c["tags"], tag_topics=sorted({TAG_RULES[t] for t in c["tags"] if t in TAG_RULES}),
            tag_expanded=sorted({EXPANDED_TAGS[t] for t in c["tags"] if t in EXPANDED_TAGS}),
            demozoo_notes=s.get("demozoo_notes", ""), video_title=s.get("video_title"),
            card_summary=card.get("summary", ""), card_highlights=card.get("highlights", []),
            comments=[x["text"] for x in s.get("csdb_comments", [])][:10],
            frames=fetch_frames(vid)))
    for i in range(0, len(rows), BATCH):
        write_jsonl(IN / f"batch_{i // BATCH + 1:02}.jsonl", rows[i:i + BATCH])
    print(f"{len(rows)} prods in {(len(rows) + BATCH - 1) // BATCH} batches; "
          f"{sum(len(r['frames']) for r in rows)} frames; inputs in {IN}")


def load():
    """Final topics per prod: the labeller's, plus tag rules, plus Tiny intros from the type."""
    inputs = {}
    for c in read_jsonl(WORK / "catalog.jsonl"):
        if c["shortlist"]:
            inputs[c["id"]] = dict(types=c["types"],
                                   tag_topics=sorted({TAG_RULES[t] for t in c["tags"] if t in TAG_RULES}),
                                   tag_expanded=sorted({EXPANDED_TAGS[t] for t in c["tags"] if t in EXPANDED_TAGS}))
    out, errors = {}, []
    for f in sorted(CARDS.glob("topics_*.jsonl")):
        for l in read_jsonl(f):
            r = inputs.get(l.get("id"))
            if not r:
                continue  # no longer shortlisted
            ids = [t.get("id") for t in l.get("topics", [])]
            bad = [t for t in ids if t not in TOPICS or t == "tiny"]
            if bad:
                errors.append(f"{l['id']}: bad topics {bad}")
            if any(not t.get("evidence") for t in l.get("topics", [])):
                errors.append(f"{l['id']}: topic without evidence")
            got = set(ids) | set(r["tag_topics"])
            if tiny(r["types"]):
                got.add("tiny")
            out[l["id"]] = dict(topics=[TOPICS[k] for k in TOPICS if k in got],
                                expanded=sorted({HARDWARE_NAMES.get(x, x) for x in set(l.get("expanded") or []) | set(r["tag_expanded"])}))
    missing = set(inputs) - set(out)
    if missing:
        errors.append(f"{len(missing)} prods unlabelled, e.g. {sorted(missing)[:5]}")
    return out, errors


def check():
    import collections
    out, errors = load()
    for e in errors:
        print(e)
    print(f"{len(out)} labelled, {len(errors)} problems")
    print(collections.Counter(t for v in out.values() for t in v["topics"]).most_common(),
          "none:", sum(not v["topics"] for v in out.values()))
    print("expanded:", collections.Counter(x for v in out.values() for x in v["expanded"]).most_common())
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    {"prepare": prepare, "check": check}[sys.argv[1]]()
