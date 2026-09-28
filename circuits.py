"""Generador de diagramas SVG de circuitos de Formula 1.

Dada una clave de circuito (ej. 'Bahrain', 'Monaco'), dibuja un trazado
estilizado cerrado con 3 sectores coloreados y la linea de meta.
No usa APIs externas: la silueta se genera proceduralmente con un seed
derivado del nombre, usando una funcion radial suave (armonicos) para
obtener curvas organicas en lugar de poligonos rigidos.
"""

from __future__ import annotations

import math
import random

W, H = 720, 460
CX, CY = W / 2, H / 2 + 8
BASE_RX = 250
BASE_RY = 148
SAMPLES = 108

SECTOR_COLORS = {
    1: "#E10600",
    2: "#FFD500",
    3: "#00B050",
}

SECTOR_TEXT = {
    1: "#FFFFFF",
    2: "#0A0A0A",
    3: "#0A0A0A",
}


def _radial_points(name: str, samples: int = SAMPLES) -> list[tuple[float, float]]:
    """Curva cerrada suave: r(theta) = 1 + suma de armonicos."""
    rng = random.Random(name)
    rx = BASE_RX * rng.uniform(0.90, 1.0)
    ry = BASE_RY * rng.uniform(0.86, 1.0)
    harmonics = []
    for k in (2, 3, 4, 5, 6):
        amp = rng.uniform(0.03, 0.13) / (k / 3)
        phase = rng.uniform(0, 2 * math.pi)
        harmonics.append((amp, phase, k))

    pts: list[tuple[float, float]] = []
    for i in range(samples):
        theta = 2 * math.pi * i / samples
        r = 1.0
        for amp, phase, k in harmonics:
            r += amp * math.sin(k * theta + phase)
        x = CX + rx * r * math.cos(theta)
        y = CY + ry * r * math.sin(theta)
        pts.append((x, y))
    return pts


def _poly_path(pts: list[tuple[float, float]]) -> str:
    if not pts:
        return ""
    cmds = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        cmds.append(f"L {x:.1f} {y:.1f}")
    return " ".join(cmds)


def _sector_paths(pts: list[tuple[float, float]]) -> list[tuple[str, str]]:
    """Divide la curva cerrada en 3 tramos continuos (S1, S2, S3)."""
    n = len(pts)
    if n < 6:
        return []
    cuts = [0, round(n / 3), round(2 * n / 3), n]
    segments: list[tuple[str, str]] = []
    for i in range(3):
        start = cuts[i]
        end = cuts[i + 1]
        chunk = pts[start:end + 1] if end < n else pts[start:] + [pts[0]]
        if len(chunk) < 2:
            continue
        segments.append((_poly_path(chunk), SECTOR_COLORS[i + 1]))
    return segments


def _curvature(pts: list[tuple[float, float]]) -> list[float]:
    """Cambio de angulo entre segmentos consecutivos (proxy de curvatura)."""
    n = len(pts)
    out: list[float] = []
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        a1 = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        a2 = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        delta = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        out.append(abs(delta))
    return out


def detect_corners(pts: list[tuple[float, float]], min_angle: float = 0.05, min_gap: int = 4) -> list[int]:
    """Devuelve los indices de los puntos de mayor curvatura (curvas)."""
    n = len(pts)
    curv = _curvature(pts)
    picked: list[tuple[int, float]] = []
    for i in range(n):
        if curv[i] < min_angle:
            continue
        window = [curv[(i + k) % n] for k in range(-min_gap, min_gap + 1)]
        if curv[i] >= max(window):
            picked.append((i, curv[i]))

    # Separacion minima entre curvas
    picked.sort(key=lambda x: -x[1])
    chosen: list[int] = []
    for idx, _ in picked:
        if all(min((idx - c) % n, (c - idx) % n) >= min_gap for c in chosen):
            chosen.append(idx)
        if len(chosen) >= 16:
            break
    return sorted(chosen)


CORNER_COLOR = "#2E90FF"


def _outward(pos: tuple[float, float], offset: float = 20.0) -> tuple[float, float]:
    dx = pos[0] - CX
    dy = pos[1] - CY
    norm = math.hypot(dx, dy) or 1.0
    return (pos[0] + dx / norm * offset, pos[1] + dy / norm * offset)


def _corner_label(pos: tuple[float, float], number: int) -> str:
    x, y = _outward(pos, 19.0)
    return (
        f'<g class="corner-tag">'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8.5" fill="#0A0A0F" opacity="0.65"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{CORNER_COLOR}" stroke="#08131F" stroke-width="1.2"/>'
        f'<text x="{x:.1f}" y="{y + 0.5:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="JetBrains Mono, monospace" font-size="8" font-weight="800" fill="#FFFFFF">{number}</text>'
        f'</g>'
    )


def _marker(pos: tuple[float, float], label: str, fill: str, text_fill: str, radius: int = 16) -> str:
    x, y = pos
    return (
        f'<g class="circuit-marker">'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius + 4}" fill="#0A0A0A" opacity="0.75"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="#0A0A0A" stroke-width="2.5"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius - 4}" fill="none" '
        f'stroke="#FFFFFF" stroke-width="1" opacity="0.25"/>'
        f'<text x="{x:.1f}" y="{y + 0.5:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="800" '
        f'letter-spacing="-0.3" fill="{text_fill}">{label}</text>'
        f'</g>'
    )


def _legend(show_corners: bool = False, corner_count: int = 0) -> str:
    items: list[tuple[str, str, str]] = [
        ("circle", SECTOR_COLORS[1], "Sector 1"),
        ("circle", SECTOR_COLORS[2], "Sector 2"),
        ("circle", SECTOR_COLORS[3], "Sector 3"),
        ("circle", "#FFFFFF", "Meta / Salida"),
    ]
    if show_corners:
        items.append(("corner", CORNER_COLOR, f"Curvas ({corner_count})"))

    item_w = 118
    box_h = 30
    gap = 6
    pad = 12
    total_w = item_w * len(items) + gap * (len(items) - 1) + pad * 2
    left = (W - total_w) / 2
    top = H - 46

    body = ""
    for i, (kind, color, label) in enumerate(items):
        x = left + pad + i * (item_w + gap)
        cy = top + box_h / 2
        if kind == "corner":
            body += (
                f'<circle cx="{x + 7}" cy="{cy}" r="7" fill="{color}" stroke="#08131F" stroke-width="1.2"/>'
                f'<text x="{x + 7}" y="{cy + 0.5}" text-anchor="middle" dominant-baseline="central" '
                f'font-family="JetBrains Mono, monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">1</text>'
            )
            tx = x + 19
        else:
            body += (
                f'<circle cx="{x + 7}" cy="{cy}" r="7" fill="{color}" stroke="#0A0A0A" stroke-width="1.5"/>'
            )
            tx = x + 19
        body += (
            f'<text x="{tx}" y="{cy + 3.5:.1f}" font-family="Chivo, sans-serif" '
            f'font-size="10.5" font-weight="700" fill="#E8E8EE">{label}</text>'
        )

    return (
        f'<g class="circuit-legend">'
        f'<rect x="{left:.1f}" y="{top}" width="{total_w}" height="{box_h}" rx="6" '
        f'fill="#101018" stroke="#2A2A35" stroke-width="1"/>'
        f'{body}'
        f'</g>'
    )


def generate_circuit_svg(
    circuit_name: str,
    subtitle: str = "",
    show_corners: bool = False,
    dim_sectors: set[str] | None = None,
    seed: str | None = None,
) -> str:
    # `circuit_name` es el texto visible; `seed` define la geometria (estable
    # aunque cambie el nombre mostrado, ej. alias vs nombre oficial de la API).
    pts = _radial_points(seed or circuit_name)
    full = _poly_path(pts) + " Z"
    dim_sectors = dim_sectors or set()

    sector_labels = {"S1": 1, "S2": 2, "S3": 3}
    sectors = "".join(
        f'<path d="{d}" fill="none" '
        f'stroke="{"#3A3A45" if any(sector_labels[s] == i + 1 for s in dim_sectors) else color}" '
        f'stroke-width="24" stroke-linejoin="round" stroke-linecap="round"/>'
        for i, (d, color) in enumerate(_sector_paths(pts))
    )

    n = len(pts)
    idx_s1 = round(n / 6)
    idx_s2 = round(3 * n / 6)
    idx_s3 = round(5 * n / 6)

    def _sector_fill(key: str, default: str) -> str:
        return "#3A3A45" if key in dim_sectors else default

    marks = (
        _marker(pts[idx_s1], "S1", _sector_fill("S1", SECTOR_COLORS[1]), SECTOR_TEXT[1])
        + _marker(pts[idx_s2], "S2", _sector_fill("S2", SECTOR_COLORS[2]), SECTOR_TEXT[2])
        + _marker(pts[idx_s3], "S3", _sector_fill("S3", SECTOR_COLORS[3]), SECTOR_TEXT[3])
        + _marker(pts[0], "S/F", "#FFFFFF", "#0A0A0A")
    )

    corner_idx = detect_corners(pts)
    corner_marks = ""
    if show_corners:
        corner_marks = "".join(
            _corner_label(pts[i], k + 1) for k, i in enumerate(corner_idx)
        )

    title = (
        f'<text x="{CX}" y="36" text-anchor="middle" '
        f'font-family="Chivo, sans-serif" font-size="18" font-weight="900" '
        f'fill="#FFFFFF" letter-spacing="1.5">{circuit_name.upper()}</text>'
    )
    sub = (
        f'<text x="{CX}" y="55" text-anchor="middle" '
        f'font-family="JetBrains Mono, monospace" font-size="10" font-weight="600" '
        f'fill="#8A92A6" letter-spacing="1.5">{subtitle.upper()}</text>'
        if subtitle
        else ""
    )

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'preserveAspectRatio="xMidYMid meet">'
        f'<defs>'
        f'<radialGradient id="trackBg" cx="50%" cy="45%" r="70%">'
        f'<stop offset="0%" stop-color="#14141C"/>'
        f'<stop offset="100%" stop-color="#0A0A0F"/>'
        f'</radialGradient>'
        f'<filter id="trackShadow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feDropShadow dx="0" dy="3" stdDeviation="6" flood-color="#000000" flood-opacity="0.6"/>'
        f'</filter>'
        f'</defs>'
        f'<rect width="{W}" height="{H}" fill="url(#trackBg)" rx="8"/>'
        f'<rect x="0" y="0" width="{W}" height="5" fill="#E10600" rx="2"/>'
        f'{title}{sub}'
        f'<g filter="url(#trackShadow)">'
        f'<path d="{full}" fill="none" stroke="#050507" stroke-width="30" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'{sectors}'
        f'</g>'
        f'<path d="{full}" fill="none" stroke="#0A0A0A" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round" opacity="0.45"/>'
        f'{corner_marks}'
        f'{marks}'
        f'{_legend(show_corners=show_corners, corner_count=len(corner_idx))}'
        f'</svg>'
    )
