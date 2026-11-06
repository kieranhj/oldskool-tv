"""Check card files against their fact sheets and the spec.

    python pipeline/validate_cards.py data/cards/batch_01.cards.jsonl [...]
    python pipeline/validate_cards.py --merge     # validate every batch and write data/cards/cards.jsonl

Exits non-zero if any card fails.
"""
import json, sys
from common import CARDS, WORK, read_jsonl

HYPE = ("stunning", "mind-blowing", "mindblowing", "legendary", "masterpiece", "!")


def check(cards_path):
    sheets_path = WORK / "card_inputs" / cards_path.name.replace(".cards", "")
    sheets = {s["id"]: s for s in read_jsonl(sheets_path)}
    errors, cards = [], []
    try:
        cards = read_jsonl(cards_path)
    except json.JSONDecodeError as e:
        return [f"{cards_path.name}: bad JSON: {e}"], []
    ids = [c.get("id") for c in cards]
    if set(ids) != set(sheets) or len(ids) != len(sheets):
        errors.append(f"{cards_path.name}: ids don't match the fact sheets "
                      f"(missing {sorted(set(sheets) - set(ids))[:5]}, extra {sorted(set(ids) - set(sheets))[:5]})")
    for c in cards:
        cid = c.get("id")
        e = lambda m: errors.append(f"{cid}: {m}")
        for k in ("summary", "why", "highlights", "quote", "basis"):
            if k not in c:
                e(f"missing {k}")
        if len((c.get("summary") or "").split()) > 50:
            e("summary over 45 words")
        if len((c.get("why") or "").split()) > 50:
            e("why over 45 words")
        if not isinstance(c.get("highlights"), list) or len(c["highlights"]) > 4:
            e("highlights must be a list of at most 4")
        if "topics" in c:
            e("topics belong in data/cards/topics_NN.jsonl (see TOPICS.md), not in the card")
        if c.get("basis") not in ("comments", "facts", "facts+knowledge"):
            e(f"bad basis {c.get('basis')}")
        text = f"{c.get('summary', '')} {c.get('why', '')} {' '.join(c.get('highlights') or [])}"
        # Names and titles may legitimately contain "!" (Bang!, JAC!, "That's Not Possible On This Platform!")
        s = sheets.get(cid, {})
        for name in [s.get("title", "")] + s.get("by", []) + s.get("credits", []) + s.get("awards", []) + s.get("placings", []):
            for part in str(name).replace(":", ",").split(","):
                part = part.strip()
                if "!" in part and part:
                    text = text.replace(part, "").replace(part.split(" (")[0], "")
        text = text.lower()
        for h in HYPE:
            if h in text:
                e(f"hype word {h!r}")
        q = c.get("quote")
        if q:
            s = sheets.get(cid, {})
            src = [x for x in s.get("csdb_comments", []) if x["user"] == q.get("user") and x["date"] == q.get("date")]
            qt = q.get("text", "").strip("…. ")
            if not src or not any(qt in x["text"] for x in src):
                e("quote is not an exact excerpt of a comment by that user on that date")
            if len(q.get("text", "")) > 210:
                e("quote over 200 chars")
    return errors, cards


def main():
    merge = "--merge" in sys.argv
    paths = sorted(CARDS.glob("batch_*.cards.jsonl")) if merge else [__import__("pathlib").Path(p) for p in sys.argv[1:]]
    all_errors, all_cards = [], []
    for p in paths:
        errs, cards = check(p)
        all_errors += errs
        all_cards += cards
    for e in all_errors:
        print(e)
    print(f"{len(all_cards)} cards, {len(all_errors)} problems")
    if all_errors:
        sys.exit(1)
    if merge:
        with open(CARDS / "cards.jsonl", "w", encoding="utf8") as f:
            for c in all_cards:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print("wrote", CARDS / "cards.jsonl")


if __name__ == "__main__":
    main()
