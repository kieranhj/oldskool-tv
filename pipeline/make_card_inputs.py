"""Build one fact sheet per shortlisted prod for the card writer, split into batches.

    python pipeline/make_card_inputs.py [--batch 50]

Writes data/work/card_inputs/batch_NN.jsonl. Prods that already have a card in data/cards/cards.jsonl are skipped,
so this only produces work for new prods.
"""
import argparse, json
from common import CACHE, CARDS, WORK, read_jsonl, write_jsonl
from fetch_csdb import parse as parse_csdb

# Demozoo bookkeeping tags that say nothing about what's on screen
NOISE_TAGS = {"unknown-author", "incomplete-credits", "no-credits-added", "no-credits-given", "cracktro-needs-extraction",
              "lost", "stages-included", "defaced-title-screen", "russian-title", "pal", "ntsc"}


def comment_sample(comments, limit=25, max_len=400):
    """Keep the substantive comments (40+ chars), spread over time, longest first within the limit."""
    subs = [c for c in comments if len(c["text"]) >= 40]
    subs.sort(key=lambda c: -len(c["text"]))
    keep = subs[:limit]
    keep.sort(key=lambda c: c["date"] or "")
    return [dict(user=c["user"], date=c["date"], text=c["text"][:max_len]) for c in keep]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=50)
    args = ap.parse_args()
    oembed = json.loads((CACHE / "oembed.json").read_text(encoding="utf8"))
    done = {c["id"] for c in read_jsonl(CARDS / "cards.jsonl")} if (CARDS / "cards.jsonl").exists() else set()
    sheets = []
    for c in read_jsonl(WORK / "catalog.jsonl"):
        if not c["shortlist"] or c["id"] in done:
            continue
        vid = next(v for v in c["videos"] if oembed.get(v, {}).get("ok"))
        cs = parse_csdb(c["csdb"]) if c["csdb"] else None
        credits = {}
        for cr in c["credits"]:
            credits.setdefault(cr["nick"], []).append(cr["category"] + (f" ({cr['role']})" if cr["role"] else ""))
        sheets.append(dict(
            id=c["id"], title=c["title"], by=c["authors"], released=c["release"], platform=c["family"],
            platforms=c["platforms"], types=c["types"],
            placings=[f"{p['rank']} in {p['compo']} at {p['party']}"
                      + ("" if str(p["year"]) in p["party"] else f" {p['year']}") for p in c["placings"]],
            awards=[f"{a['status']}: {a['category']} ({a['event']})" for a in c["awards"]],
            tags=[t for t in c["tags"] if t not in NOISE_TAGS],
            credits=[f"{n}: {', '.join(v)}" for n, v in credits.items()][:20],
            demozoo_notes=c["notes"][:1200],
            pouet_votes=c["votes"],
            video_title=oembed[vid].get("title"), video_channel=oembed[vid].get("channel"),
            csdb_rating=cs["rating"] if cs else None,
            csdb_comments=comment_sample(cs["comments"]) if cs else [],
        ))
    out = WORK / "card_inputs"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("batch_*.jsonl"):
        f.unlink()
    for i in range(0, len(sheets), args.batch):
        write_jsonl(out / f"batch_{i // args.batch + 1:02}.jsonl", sheets[i:i + args.batch])
    print(f"{len(sheets)} fact sheets in {(len(sheets) + args.batch - 1) // args.batch} batches;"
          f" {sum(bool(s['csdb_comments']) for s in sheets)} with CSDb comments")


if __name__ == "__main__":
    main()
