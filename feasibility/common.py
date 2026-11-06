"""Shared bits for the feasibility scripts."""
import re

# Pouet platform names counted as 8-bit (CPU is 8-bit: 6502/65xx, Z80, 6809, 8080 families).
POUET_8BIT = {
    "Commodore 64", "ZX Spectrum", "Atari XL/XE", "Amstrad CPC", "C16/116/plus4", "Apple II",
    "Atari VCS", "VIC 20", "Gameboy Color", "Gameboy", "ZX Enhanced", "Amstrad Plus", "Atari Lynx",
    "MSX", "MSX 2", "MSX 2 plus", "MSX Turbo-R", "NES/Famicom", "SAM Coup\ufffd", "SAM Coupé", "ZX-81",
    "Vector-06c", "SEGA Master System", "Thomson", "Oric", "BBC Micro", "Vectrex", "Sharp MZ",
    "Commodore PET", "TI-8x (Z80)", "Commodore 128", "C64 DTV", "Enterprise", "TRS-80/CoCo/Dragon",
    "NEC TurboGrafx/PC Engine", "KC-85", "Atari 7800", "Spectravideo 3x8", "SEGA Game Gear",
    "Pokemon Mini", "C64DX/C65/MEGA65",
}

YT_RE = re.compile(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})")

def youtube_ids(text):
    return YT_RE.findall(text or "")

# Demozoo platform ids counted as 8-bit (platforms_platform.id).
DEMOZOO_8BIT = {2, 3, 16, 21, 25, 31, 36, 37, 38, 41, 42, 43, 44, 45, 49, 51, 53, 54, 55, 61, 63, 65, 66,
                67, 69, 70, 74, 75, 82, 83, 86, 87, 88, 90, 91, 101, 102, 105}
