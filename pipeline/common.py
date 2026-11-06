"""Shared constants and helpers for the pipeline."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, WORK, CACHE, CARDS = (ROOT / "data" / d for d in ("raw", "work", "cache", "cards"))
SITE_DATA = ROOT / "site" / "data"
UA = {"User-Agent": "oldskool-tv-pipeline (https://github.com/kieranhj)"}

# Pouet platform names counted as 8-bit (CPU is 8-bit: 6502/65xx, Z80, 6809, 8080 families).
POUET_8BIT = {
    "Commodore 64", "ZX Spectrum", "Atari XL/XE", "Amstrad CPC", "C16/116/plus4", "Apple II",
    "Atari VCS", "VIC 20", "Gameboy Color", "Gameboy", "ZX Enhanced", "Amstrad Plus", "Atari Lynx",
    "MSX", "MSX 2", "MSX 2 plus", "MSX Turbo-R", "NES/Famicom", "SAM Coup�", "SAM Coupé", "ZX-81",
    "Vector-06c", "SEGA Master System", "Thomson", "Oric", "BBC Micro", "Vectrex", "Sharp MZ",
    "Commodore PET", "TI-8x (Z80)", "Commodore 128", "C64 DTV", "Enterprise", "TRS-80/CoCo/Dragon",
    "NEC TurboGrafx/PC Engine", "KC-85", "Atari 7800", "Spectravideo 3x8", "SEGA Game Gear",
    "Pokemon Mini", "C64DX/C65/MEGA65",
}

# Demozoo platform ids counted as 8-bit (platforms_platform.id).
DEMOZOO_8BIT = {2, 3, 16, 21, 25, 31, 36, 37, 38, 41, 42, 43, 44, 45, 49, 51, 53, 54, 55, 61, 63, 65, 66,
                67, 69, 70, 74, 75, 82, 83, 86, 87, 88, 90, 91, 101, 102, 105}

# Display families: several Demozoo platforms browse together.
FAMILY = {
    "Commodore 64": "Commodore 64", "Commodore 64-DTV": "Commodore 64", "Commodore 128": "Commodore 64",
    "ZX Spectrum": "ZX Spectrum", "ZX Spectrum Enhanced": "ZX Spectrum",
    "Amstrad CPC": "Amstrad CPC", "Amstrad Plus": "Amstrad CPC",
    "Atari 8 bit": "Atari 8-bit",
    "Nintendo Game Boy (GB)": "Game Boy", "Nintendo Game Boy Color (GBC)": "Game Boy",
    "Nintendo Entertainment System (NES)": "NES",
    "Atari 2600 Video Computer System (VCS)": "Atari VCS",
    "Commodore 16/Plus 4": "C16/Plus 4", "Commodore VIC-20": "VIC-20",
    "Sharp MZ-700": "Sharp MZ", "Sharp MZ-800": "Sharp MZ",
}
POUET_FAMILY = {
    "Commodore 64": "Commodore 64", "C64 DTV": "Commodore 64", "Commodore 128": "Commodore 64",
    "ZX Spectrum": "ZX Spectrum", "ZX Enhanced": "ZX Spectrum", "Amstrad CPC": "Amstrad CPC",
    "Amstrad Plus": "Amstrad CPC", "Atari XL/XE": "Atari 8-bit", "Gameboy": "Game Boy",
    "Gameboy Color": "Game Boy", "NES/Famicom": "NES", "Atari VCS": "Atari VCS", "C16/116/plus4": "C16/Plus 4",
    "VIC 20": "VIC-20", "Sharp MZ": "Sharp MZ", "BBC Micro": "BBC Micro", "Apple II": "Apple II",
    "MSX": "MSX", "MSX 2": "MSX", "MSX 2 plus": "MSX", "MSX Turbo-R": "MSX", "Atari Lynx": "Atari Lynx",
    "Oric": "Oric", "Vectrex": "Vectrex", "SAM Coup�": "SAM Coupé", "SAM Coupé": "SAM Coupé", "ZX-81": "ZX81",
    # Pouet-only names mapped to Demozoo's spelling so both sources browse under one family
    "Vector-06c": "Vector-06C", "SEGA Master System": "Sega Master System", "Thomson": "Thomson",
    "Commodore PET": "Commodore PET", "Enterprise": "Enterprise", "TRS-80/CoCo/Dragon": "TRS-80",
    "NEC TurboGrafx/PC Engine": "NEC PC Engine", "KC-85": "KC 85/Robotron KC 87",
    "Atari 7800": "Atari 7800 ProSystem", "SEGA Game Gear": "Sega Game Gear", "TI-8x (Z80)": "TI-8x (Z80)",
}


def family(demozoo_platform_name):
    return FAMILY.get(demozoo_platform_name, demozoo_platform_name)


# Production types worth watching (Demozoo names; any "... Intro" size class also counts).
WATCH_TYPES_DZ = {"Demo", "Intro", "Cracktro", "Invitation"}
WATCH_TYPES_POUET = {"demo", "intro", "cracktro", "invitation", "dentro", "32b", "64b", "128b", "256b", "512b",
                     "1k", "2k", "4k", "8k", "16k", "32k", "40k", "64k", "80k", "96k", "100k"}


def watchable_dz(type_name):
    return type_name in WATCH_TYPES_DZ or type_name.lower().endswith("intro")


YT_RE = re.compile(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})")


def youtube_ids(text):
    return YT_RE.findall(text or "")


def read_jsonl(path):
    with open(path, encoding="utf8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
