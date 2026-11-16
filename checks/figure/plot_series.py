#!/usr/bin/env python3
"""Write one SVG line chart from a two-column integer CSV.

Stdlib only. Coordinates are integer arithmetic, so the SVG bytes do not
depend on matplotlib, fonts, or locale. This is a mechanical figure, not a
publication graphic.
"""
from __future__ import annotations

import sys
from pathlib import Path


WIDTH = 320
HEIGHT = 180
PAD = 24


def _integers(text: str) -> list[tuple[int, int]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0].replace(" ", "") != "x,y":
        raise ValueError("header must be x,y")
    rows: list[tuple[int, int]] = []
    for line in lines[1:]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 2:
            raise ValueError("each row needs two integer cells")
        for part in parts:
            if part[0:1] in "+-":
                digits = part[1:]
            else:
                digits = part
            if not digits.isdigit():
                raise ValueError("cells must be integers")
        rows.append((int(parts[0]), int(parts[1])))
    if len(rows) < 2:
        raise ValueError("need at least two points")
    return rows


def _hundredths(value: int, lo: int, hi: int, out_lo: int, out_hi: int) -> int:
    if hi == lo:
        return out_lo * 100
    return out_lo * 100 + (value - lo) * (out_hi - out_lo) * 100 // (hi - lo)


def _fmt(hundredths: int) -> str:
    sign = "-" if hundredths < 0 else ""
    magnitude = abs(hundredths)
    return f"{sign}{magnitude // 100}.{magnitude % 100:02d}"


def render_svg(csv_text: str) -> str:
    rows = _integers(csv_text)
    xs = [row[0] for row in rows]
    ys = [row[1] for row in rows]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    left, right = PAD, WIDTH - PAD
    top, bottom = PAD, HEIGHT - PAD
    points = []
    for x_value, y_value in rows:
        sx = _fmt(_hundredths(x_value, min_x, max_x, left, right))
        sy = _fmt(_hundredths(y_value, min_y, max_y, bottom, top))
        points.append(f"{sx},{sy}")
    point_attr = " ".join(points)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">\n'
        f'  <polyline fill="none" stroke="#000000" stroke-width="2" points="{point_attr}"/>\n'
        "</svg>\n"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: plot_series.py data.csv out.svg", file=sys.stderr)
        return 2
    source = Path(argv[1])
    destination = Path(argv[2])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_svg(source.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
