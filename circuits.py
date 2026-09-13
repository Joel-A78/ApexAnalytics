"""Generador de diagramas SVG de circuitos F1.

Dada una clave de circuito (ej. 'Bahrain', 'Monaco'), dibuja un trazado
estilizado cerrado con 3 sectores coloreados y la linea de meta.
No usa APIs externas: el trazado se genera proceduralmente con un seed
derivado del nombre para que cada circuito tenga una silueta distinta.
"""

from __future__ import annotations

import math
import random

W, H = 640, 420
CX, CY = W / 2, H / 2
BASE_RX = 260
BASE_RY = 160

SECTOR_COLORS = {
    1: "#E10600",
    2: "#FFD500",
    3: "#00B050",
}


def _seeded_points(name: str, n: int) -> list[tuple[float, float]]:
    rng = random.Random(name)
    pts: list[tuple[float, float]] = []
    for i in range(n):
        angle = (i / n) * 2 * math.pi + rng.uniform(-0.15, 0.15)
        rx = BASE_RX * rng.uniform(0.55, 1.05)
        ry = BASE_RY * rng.uniform(0.45, 0.95)
        x = CX + rx * math.cos(angle)
        y = CY + ry * math.sin(angle)
        pts.append((x, y))
    return pts


def _closed_smooth_path(pts: list[tuple[float, float]]) -> str:
    n = len(pts)
    cmds: list[str] = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        cmds.append(f"C {c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    cmds.append("Z")
    return " ".join(cmds)


def _path_lengths(pts: list[tuple[float, float]]) -> list[float]:
    out = [0.0]
    total = 0.0
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        total += math.hypot(b[0] - a[0], b[1] - a[1])
        out.append(total)
    return out


def _point_at_fraction(pts: list[tuple[float, float]], lengths: list[float], frac: float) -> tuple[float, float]:
    target = lengths[-1] * frac
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        seg_len = lengths[i + 1] - lengths[i]
        if lengths[i] <= target <= lengths[i + 1] and seg_len > 0:
            t = (target - lengths[i]) / seg_len
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    return pts[0]


def generate_circuit_svg(circuit_name: str) -> str:
    n_points = max(6, min(12, sum(ord(c) for c in circuit_name) % 5 + 8))
    pts = _seeded_points(circuit_name, n_points)
    full_path = _closed_smooth_path(pts)
    lengths = _path_lengths(pts)

    p_start = pts[0]
    p_s1 = _point_at_fraction(pts, lengths, 1 / 3)
    p_s2 = _point_at_fraction(pts, lengths, 2 / 3)

    sector_marks = ""
    for idx, (pos, label) in enumerate([(p_start, "S/F"), (p_s1, "S1"), (p_s2, "S2")], start=1):
        color = "#FFFFFF" if label == "S/F" else SECTOR_COLORS.get(idx, "#E10600")
        sector_marks += (
            f'<g class="circuit-marker">'
            f'<circle cx="{pos[0]:.1f}" cy="{pos[1]:.1f}" r="14" fill="{color}" stroke="#0A0A0A" stroke-width="2"/>'
            f'<text x="{pos[0]:.1f}" y="{pos[1]:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="JetBrains Mono, monospace" font-size="10" font-weight="800" fill="#0A0A0A">{label}</text>'
            f'</g>'
        )

    s3_pos = _point_at_fraction(pts, lengths, 0.92)
    sector_marks += (
        f'<g class="circuit-marker-s3">'
        f'<circle cx="{s3_pos[0]:.1f}" cy="{s3_pos[1]:.1f}" r="14" fill="{SECTOR_COLORS[3]}" stroke="#0A0A0A" stroke-width="2"/>'
        f'<text x="{s3_pos[0]:.1f}" y="{s3_pos[1]:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="JetBrains Mono, monospace" font-size="10" font-weight="800" fill="#0A0A0A">S3</text>'
        f'</g>'
    )

    legend = (
        f'<g class="circuit-legend" transform="translate(20, {H - 56})">'
        f'<rect width="180" height="44" rx="4" fill="#15151E" stroke="#1F1F1F" stroke-width="1"/>'
        f'<circle cx="14" cy="14" r="6" fill="{SECTOR_COLORS[1]}"/>'
        f'<text x="26" y="18" font-family="Chivo, sans-serif" font-size="10" font-weight="700" fill="#FFFFFF">Sector 1</text>'
        f'<circle cx="14" cy="32" r="6" fill="{SECTOR_COLORS[2]}"/>'
        f'<text x="26" y="36" font-family="Chivo, sans-serif" font-size="10" font-weight="700" fill="#FFFFFF">Sector 2</text>'
        f'<circle cx="100" cy="14" r="6" fill="{SECTOR_COLORS[3]}"/>'
        f'<text x="112" y="18" font-family="Chivo, sans-serif" font-size="10" font-weight="700" fill="#FFFFFF">Sector 3</text>'
        f'<circle cx="100" cy="32" r="6" fill="#FFFFFF"/>'
        f'<text x="112" y="36" font-family="Chivo, sans-serif" font-size="10" font-weight="700" fill="#FFFFFF">Start/Finish</text>'
        f'</g>'
    )

    title = (
        f'<text x="{CX}" y="32" text-anchor="middle" '
        f'font-family="Chivo, sans-serif" font-size="16" font-weight="900" '
        f'fill="#FFFFFF" letter-spacing="2">{circuit_name.upper()}</text>'
    )

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'preserveAspectRatio="xMidYMid meet">'
        f'<rect width="{W}" height="{H}" fill="#0A0A0A" rx="6"/>'
        f'<rect x="0" y="0" width="{W}" height="6" fill="#E10600"/>'
        f'{title}'
        f'<path d="{full_path}" fill="none" stroke="#2D2D35" stroke-width="22" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<path d="{full_path}" fill="none" stroke="#C0C0C0" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        f'{sector_marks}'
        f'{legend}'
        f'</svg>'
    )
