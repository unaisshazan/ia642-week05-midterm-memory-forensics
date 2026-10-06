#!/usr/bin/env python3
"""Render terminal-style evidence screenshots from live Volatility outputs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "figures"
SRC = Path(__file__).resolve().parent / "output"

SHOTS = [
    ("fig_A1_imageinfo.png", "wcry/A1_imageinfo.txt", "A1 | vol26.exe imageinfo | wcry.vmem", 14),
    ("fig_A2_pstree.png", "wcry/A2_pstree.txt", "A2 | vol26.exe pstree | wcry.vmem", 16),
    ("fig_A3_psxview.png", "wcry/A3_psxview.txt", "A3 | vol26.exe psxview | wcry.vmem", 14),
    ("fig_A5_sockets.png", "wcry/A5_sockets.txt", "A5 | vol26.exe sockets | wcry.vmem", 12),
    ("fig_B2_pslist.png", "stuxnet/B2_pslist.txt", "B2 | vol26.exe pslist | stuxnet.vmem", 16),
    ("fig_B5_dlllist_680.png", "stuxnet/B5_dlllist_680.txt", "B5/B6 | vol26.exe dlllist -p 680", 14),
    ("fig_B7_malfind_868.png", "stuxnet/B7_malfind_868.txt", "B7 | vol26.exe malfind -p 868", 16),
    ("fig_B8_hashes.png", "stuxnet/B8_dump_hashes.txt", "B8 | sha256sum process.*.dmp", 10),
    ("fig_B10_ldrmodules.png", "stuxnet/B10_ldrmodules_1928.txt", "B10 | vol26.exe ldrmodules -p 1928", 12),
]


def decode(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe"):
        text = raw.decode("utf-16-le")
    elif raw.startswith(b"\xef\xbb\xbf"):
        text = raw[3:].decode("utf-8", errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")
    return text.replace("\x00", "").replace("\r\n", "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("consola.ttf", 15)
        title_f = ImageFont.truetype("consolab.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        title_f = font

    bg, fg, title_c = (12, 16, 24), (220, 230, 240), (120, 200, 140)
    for name, rel, title, max_lines in SHOTS:
        path = SRC / rel.replace("/", "\\")
        if not path.is_file():
            print("missing", rel)
            continue
        all_lines = decode(path.read_bytes()).splitlines()
        lines = all_lines[:max_lines]
        if len(all_lines) > max_lines:
            lines.append("... (truncated for figure)")

        pad, line_h, width = 16, 20, 980
        rows: list[str] = []
        for ln in lines:
            while len(ln) > 108:
                rows.append(ln[:108])
                ln = ln[108:]
            rows.append(ln)

        height = pad * 2 + 36 + line_h * len(rows)
        img = Image.new("RGB", (width, height), bg)
        dr = ImageDraw.Draw(img)
        dr.text((pad, 10), title, fill=title_c, font=title_f)
        dr.line((pad, 32, width - pad, 32), fill=(40, 60, 50), width=1)
        y = 40
        for ln in rows:
            dr.text((pad, y), ln, fill=fg, font=font)
            y += line_h
        img.save(OUT / name)
        print("wrote", name)


if __name__ == "__main__":
    main()
