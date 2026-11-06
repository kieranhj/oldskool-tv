# Topics

Five topics for browsing, plus an **expanded-hardware** badge. They're limited to what can be decided from tags,
the prod type and YouTube's three stills, without user comments. Topics that need someone to have watched it
(music-first, design and story, humour, specific video-chip tricks) wait until there are comments to go on.

| id | Name | Covers | Usual evidence |
|---|---|---|---|
| `3d` | 3D & vectors | Filled, shaded or textured polygons, wireframes, dot balls, glenz, particles | frames, tags |
| `effects` | 2D effects | Rasters and colour bars, plasma, rotozoomers, tunnels, twisters, scrollers, fractals | frames, tags |
| `pixel-art` | Pixel art | Big hand-drawn pictures and slideshows; graphics are the point | frames, tags |
| `text-mode` | Text-mode art | PETSCII, ATASCII, teletext, character-mode art and animation | tags, frames |
| `tiny` | Tiny intros | Size-limited intros of 4K or less | prod type (set in code, not judged) |

A prod can have any number of topics, including none.

## Expanded hardware badge

`expanded`: a list of requirements beyond the stock machine, e.g. `REU`, `VBXE`, `2SID`, `128K`, `Spectrum Next`,
`Amstrad Plus`, `BBC Master`, `MSX2`. Leave it empty for stock machines.

## Evidence

Every topic carries evidence: `tag:<name>`, `comment:<user> <date>`, `frame:<1|2|3>`, `title`, `notes` or
`knowledge`. Claim a topic only with evidence. Ignore stills that show only a party logo, title card or rating card.

## Labelling

Input: `data/work/topic_inputs/batch_NN.jsonl`, one prod per line, with tags, `tag_topics` (already applied in
code), the existing card's summary and highlights, up to 10 CSDb comments, and `frames` (paths to three JPEGs:
look at all of them). Output: `data/cards/topics_NN.jsonl`, one line per input prod, same order:

```json
{"id": "dz6309", "topics": [{"id": "3d", "evidence": ["frame:2"]}, {"id": "pixel-art", "evidence": ["frame:1", "frame:3"]}], "expanded": []}
```

- Use only `3d`, `effects`, `pixel-art`, `text-mode`. Never `tiny`: that's set from the prod type.
- Claim a topic when it's a visible or documented part of the prod, not for a passing moment you can only guess
  at. An empty list is fine.
- `pixel-art` is for big hand-drawn pictures that are a feature of the prod, not small logos or fonts.
- `expanded` lists hardware beyond the stock machine only when the tags, title, notes or comments say so.
- Check with `python pipeline/label_topics.py check`.
