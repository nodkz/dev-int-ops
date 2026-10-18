#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""DevIntOps diagrams in the ribbon style. Writes SVGs into site/assets; tools/render.sh turns them into PNGs."""
import bisect
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "site" / "assets" / "diagrams"
ASSETS.mkdir(parents=True, exist_ok=True)
CREDIT = "devintops.org  ·  © 2026 Pavel Chertorogov  ·  CC BY 4.0"

SANS = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
BG, INK, BODY, MUTED, RULE = "#FFFFFF", "#0F172A", "#4B5563", "#6B7280", "#E5E7EB"
AMBER = "#B45309"
LOOPS = {
    "dev": dict(light="#2EB8C4", dark="#0A7782", text="#087481"),
    "ops": dict(light="#5577FF", dark="#1D38C2", text="#2442C8"),
    "int": dict(light="#A57BFF", dark="#5F2FD8", text="#5A2CCF"),
}
STAGES = {
    "dev": ("Plan", "Code", "Build", "Test"),
    "ops": ("Release", "Deploy", "Operate", "Monitor"),
    "int": ("Understand", "Predict", "Orchestrate", "Learn"),
}
DESCRIPTIONS = {
    "Plan": ("Turn goals and evidence into", "a roadmap and specs."),
    "Code": ("Implement the change, with", "agents and people in one repo."),
    "Build": ("Turn code into deployable", "artifacts, automatically."),
    "Test": ("Check the change works before", "anyone depends on it."),
    "Release": ("Package a tested build into a", "versioned release, ready to ship."),
    "Deploy": ("Roll out step by step through", "rings and feature flags."),
    "Operate": ("Keep the system available,", "scaled and within budget."),
    "Monitor": ("Watch real behavior: telemetry,", "errors and user signals."),
    "Understand": ("Read goals, context and outcomes:", "what is asked, known and unclear."),
    "Predict": ("Weigh options, including no action,", "and select one within the limits."),
    "Orchestrate": ("Send each decision to the stage", "or agent allowed to act on it."),
    "Learn": ("Compare expected with actual and", "keep, revise or retract the lesson."),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=16, weight=400, fill=INK, anchor="start", ls=0):
    extra = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def rich(x, y, parts, size=20, anchor="middle"):
    spans = "".join(f'<tspan fill="{f}" font-weight="{w}">{esc(t)}</tspan>' for t, f, w in parts)
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" text-anchor="{anchor}" '
            f'xml:space="preserve">{spans}</text>')


def svg_defs(defs=""):
    return (f'<defs>{defs}<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feDropShadow dx="0" dy="6" stdDeviation="9" flood-color="#0F172A" flood-opacity="0.18"/></filter>'
            f'<radialGradient id="hubg" cx="40%" cy="35%" r="75%"><stop offset="0" stop-color="#26324A"/>'
            f'<stop offset="1" stop-color="#0B1220"/></radialGradient></defs>')


def svg_open(w, h, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + svg_defs(defs) + f'<rect width="{w}" height="{h}" fill="{BG}"/>')


def verbs(x, y, size=22, full=True):
    d, o, i = ("Development", "Operations", "Intelligence") if full else ("Dev", "Ops", "Int")
    sep = ("    ·    ", BODY, 400)
    return rich(x, y, [
        (d, LOOPS["dev"]["text"], 700), (" changes the implementation", BODY, 400), sep,
        (o, LOOPS["ops"]["text"], 700), (" changes how it runs", BODY, 400), sep,
        (i, LOOPS["int"]["text"], 700), (" changes how it decides", BODY, 400)], size=size)


class Track:
    """A sampled centre line with cumulative arc length."""

    def __init__(self, pts, closed=False):
        self.pts = pts + [pts[0]] if closed else list(pts)
        self.closed = closed
        self.cum = [0.0]
        for (x0, y0), (x1, y1) in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + math.hypot(x1 - x0, y1 - y0))
        self.length = self.cum[-1]

    def at(self, s):
        s = s % self.length if self.closed else min(max(s, 0.0), self.length)
        i = max(0, min(bisect.bisect_right(self.cum, s) - 1, len(self.pts) - 2))
        seg = (self.cum[i + 1] - self.cum[i]) or 1e-9
        f = (s - self.cum[i]) / seg
        (x0, y0), (x1, y1) = self.pts[i], self.pts[i + 1]
        return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, (x1 - x0) / seg, (y1 - y0) / seg

    def side(self, s, d):
        x, y, dx, dy = self.at(s)
        return x + dy * d, y - dx * d

    @staticmethod
    def steps(s0, s1, step=2.5):
        n = max(2, int(abs(s1 - s0) / step) + 1)
        return [s0 + (s1 - s0) * k / (n - 1) for k in range(n)]


def poly(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def chevron(track, s0, s1, width, head, notch=True):
    """One ribbon segment: notched (or flat) tail at s0, pointed head just past s1."""
    half = width / 2
    left = [track.side(s, half) for s in Track.steps(s0, s1)]
    right = [track.side(s, -half) for s in Track.steps(s1, s0)]
    tail = [track.at(s0 + head)[:2]] if notch else []
    return poly(left + [track.at(s1 + head)[:2]] + right + tail) + " Z"


def band_text(track, s_mid, label, size, path_id, centre=None, fill="#FFFFFF", span=320, weight=700):
    """White label running along the ribbon, flipped so it never reads upside down."""
    s_a, s_b = s_mid - span / 2, s_mid + span / 2
    if not track.closed:
        s_a, s_b = max(0.0, s_a), min(track.length, s_b)
    x, y, dx, dy = track.at(s_mid)
    if abs(dx) >= 0.45 or centre is None:
        flip = dx < 0
    else:
        ox, oy = x - centre[0], y - centre[1]
        flip = (dy * ox - dx * oy) < 0  # keep the glyph tops pointing away from the ring centre
    pts = [track.at(s)[:2] for s in Track.steps(s_a, s_b, 2.0)]
    offset = s_mid - s_a
    if flip:
        pts.reverse()
        offset = s_b - s_mid
    return (f'<path id="{path_id}" d="{poly(pts)}" fill="none"/>'
            f'<text font-family="{SANS}" font-size="{size}" font-weight="{weight}" fill="{fill}" dy="{size * 0.35:.1f}">'
            f'<textPath href="#{path_id}" startOffset="{offset:.1f}" text-anchor="middle">{esc(label)}</textPath></text>')


def arc_text(cx, cy, radius, psi_mid, label, size, fill, path_id, span=150, ls=2.5, weight=400):
    """Label curving around the outside of a ring, readable at any angle."""
    lower = math.sin(math.radians(psi_mid)) > 0.3
    r = radius + size * 0.72 if lower else radius
    sign = -1 if lower else 1
    pts = []
    for k in range(181):
        a = math.radians(psi_mid - sign * span / 2 + sign * span * k / 180)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return (f'<path id="{path_id}" d="{poly(pts)}" fill="none"/>'
            f'<text font-family="{SANS}" font-size="{size}" font-weight="{weight}" fill="{fill}" letter-spacing="{ls}">'
            f'<textPath href="#{path_id}" startOffset="50%" text-anchor="middle">{esc(label)}</textPath></text>')


def circle_pts(cx, cy, r, psi0, sweep, n=900):
    return [(cx + r * math.cos(math.radians(psi0 + sweep * k / n)),
             cy + r * math.sin(math.radians(psi0 + sweep * k / n))) for k in range(n + 1)]


def ribbon_segments(defs, out, track, spans, keys, labels, width, head, uid, size, centre=None, opacity=1.0,
                    first_flat=False, hot=None):
    """hot: optional list of keys; each segment is then wrapped in a group the site's explorer can address."""
    for i, ((s0, s1), key, label) in enumerate(zip(spans, keys, labels)):
        col = LOOPS[key]
        (ax, ay, _, _), (bx, by, _, _) = track.at(s0), track.at(s1 + head)
        gid = f"{uid}g{i}"
        defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{ax:.1f}" y1="{ay:.1f}" '
                    f'x2="{bx:.1f}" y2="{by:.1f}"><stop offset="0" stop-color="{col["light"]}"/>'
                    f'<stop offset="1" stop-color="{col["dark"]}"/></linearGradient>')
        notch = not (first_flat and i == 0)
        if hot:
            out.append(f'<g class="hot seg" data-key="{hot[i]}">')
        out.append(f'<path d="{chevron(track, s0, s1, width, head, notch)}" fill="url(#{gid})" opacity="{opacity}"/>')
        if label:
            out.append(band_text(track, (s0 + s1) / 2 + head / 2, label, size, f"{uid}t{i}", centre))
        if hot:
            out.append("</g>")


def ring_loop(defs, out, uid, key, hub, theta, dist, r, width, direction, size, gap_start, gap_tip, gap=7, hot=False):
    """A loop that leaves the hub, runs round its own ring of stages and comes back into it."""
    cx = hub[0] + dist * math.cos(math.radians(theta))
    cy = hub[1] + dist * math.sin(math.radians(theta))
    psi_start = theta + 180 + direction * gap_start
    sweep = 360 - gap_start - gap_tip
    track = Track(circle_pts(cx, cy, r, psi_start, direction * (sweep + 30)))
    head = width * 0.42
    total = math.radians(sweep) * r
    stages = STAGES[key]
    n = len(stages)
    seg = (total - gap * (n - 1) - head) / n
    spans = [(k * (seg + gap), k * (seg + gap) + seg) for k in range(n)]
    ribbon_segments(defs, out, track, spans, [key] * n, stages, width, head, uid, size, centre=(cx, cy),
                    first_flat=True, hot=[s.lower() for s in stages] if hot else None)
    x0, y0, dx0, dy0 = track.at(0.0)
    x1, y1, dx1, dy1 = track.at(spans[-1][1] + head)
    return dict(cx=cx, cy=cy, psi_start=psi_start, sweep=sweep, direction=direction,
                start=(x0, y0), start_dir=(dx0, dy0), end=(x1, y1), end_dir=(dx1, dy1))


def hub_disc(cx, cy, r):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r + 9}" fill="#FFFFFF" filter="url(#soft)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#hubg)"/>')


def hub_label(x, y, size, fill="#FFFFFF"):
    return text(x, y + size * 0.36, "System", size, 700, fill, "middle")


# Geometry of the three-loops diagram, shared by the static figure and the site's interactive model.
THREE_HUB, THREE_HUB_R = (1000, 665), 112
THREE_R, THREE_WIDTH, THREE_DIST, THREE_GAP_START, THREE_GAP_TIP = 180, 74, 268, 20, 20
THREE_LOOPS = [
    ("dev", 210, -1, "Development", ("Flow", "and quality"),
     ("Continuous Integration", "Continuous Delivery")),
    ("ops", 330, 1, "Operations", ("Stability", "and observability"),
     ("Continuous Deployment", "Continuous Feedback")),
    ("int", 90, 1, "Intelligence", ("Memory", "and judgment"),
     ("Continuous Reasoning", "Continuous Adaptation")),
]


def three_loops():
    w, h = 2000, 1535
    (hx, hy), hub_r = THREE_HUB, THREE_HUB_R
    r, width, dist, gap_start, gap_tip = THREE_R, THREE_WIDTH, THREE_DIST, THREE_GAP_START, THREE_GAP_TIP
    defs, out = [], []
    out.append(text(w / 2, 100, "Three loops around one system", 52, 800, INK, "middle"))
    out.append(verbs(w / 2, 152, 22))

    rings = {}
    for key, theta, direction, name, core, procs in THREE_LOOPS:
        ring = ring_loop(defs, out, key, key, (hx, hy), theta, dist, r, width, direction, 27, gap_start, gap_tip)
        rings[key] = ring
        col = LOOPS[key]
        start, sweep = ring["psi_start"], ring["sweep"]
        mids = (start + direction * sweep / 4, start + direction * sweep * 3 / 4)
        for j, (proc, psi) in enumerate(zip(procs, mids)):
            out.append(arc_text(ring["cx"], ring["cy"], r + width / 2 + 14, psi, proc, 21, col["text"], f"{key}p{j}"))
        out.append(text(ring["cx"], ring["cy"] - 18, name, 30, 800, col["text"], "middle"))
        out.append(text(ring["cx"], ring["cy"] + 20, core[0], 20, 500, INK, "middle"))
        out.append(text(ring["cx"], ring["cy"] + 46, core[1], 20, 500, INK, "middle"))
    out.append(hub_disc(hx, hy, hub_r))
    out.append(hub_label(hx, hy, 38))

    def entry(x, y, stage, key, anchor="start"):
        col = LOOPS[key]
        l1, l2 = DESCRIPTIONS[stage]
        return (text(x, y, stage, 27, 700, col["text"], anchor)
                + text(x, y + 34, l1, 19, 400, BODY, anchor) + text(x, y + 61, l2, 19, 400, BODY, anchor))

    for k, stage in enumerate(STAGES["dev"]):
        out.append(entry(90, 322 + k * 142, stage, "dev"))
    for k, stage in enumerate(STAGES["ops"]):
        out.append(entry(1600, 322 + k * 142, stage, "ops"))
    for k, stage in enumerate(STAGES["int"]):
        out.append(entry(355 + k * 430, 1265, stage, "int", "middle"))

    out.append(f'<line x1="300" y1="1385" x2="1700" y2="1385" stroke="{RULE}" stroke-width="2"/>')
    out.append(text(w / 2, 1443, "We are not just adding AI to the software development lifecycle.", 26, 400, BODY, "middle"))
    out.append(text(w / 2, 1483, "We are adding intelligence to the lifecycle of software itself.", 26, 800, INK, "middle"))
    out.append(text(w - 40, h - 18, CREDIT, 14, 500, MUTED, "end"))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


def three_loops_interactive():
    """The rings of three_loops() without the text around them, for the site's model explorer.

    Same geometry, colors and labels as the static figure. Every stage, continuous process, loop core and the
    hub sits in a group with class "hot" and a data-key that site/assets/explorer.js uses; process labels and
    loop cores get invisible hit areas so a pointer does not have to land on thin text.
    """
    (hx, hy), hub_r = THREE_HUB, THREE_HUB_R
    r, width = THREE_R, THREE_WIDTH
    proc_size, proc_ls = 21, 2.5
    radius = r + width / 2 + 14
    defs, out, centres = [], [], []
    for key, theta, direction, name, core, procs in THREE_LOOPS:
        col = LOOPS[key]
        out.append(f'<g class="loop" data-loop="{key}">')
        ring = ring_loop(defs, out, f"x{key}", key, (hx, hy), theta, THREE_DIST, r, width, direction, 27,
                         THREE_GAP_START, THREE_GAP_TIP, hot=True)
        cx, cy = ring["cx"], ring["cy"]
        start, sweep = ring["psi_start"], ring["sweep"]
        for j, (proc, psi) in enumerate(zip(procs, (start + direction * sweep / 4, start + direction * sweep * 3 / 4))):
            half = math.degrees(len(proc) * (proc_size * 0.56 + proc_ls) / 2 / radius) + 5
            hit = poly(circle_pts(cx, cy, radius + proc_size * 0.36, psi - half, 2 * half, 60))
            out.append(f'<g class="hot proc" data-key="{proc.split()[-1].lower()}">'
                       f'<path class="hit" d="{hit}" fill="none" stroke="#000000" stroke-opacity="0" stroke-width="40" '
                       f'stroke-linecap="round"/>'
                       + arc_text(cx, cy, radius, psi, proc, proc_size, col["text"], f"x{key}p{j}") + "</g>")
        out.append(f'<g class="hot core" data-key="{key}">'
                   f'<circle class="hit" cx="{cx:.1f}" cy="{cy:.1f}" r="{r - width / 2 - 4:.1f}" fill="#FFFFFF" fill-opacity="0"/>'
                   + text(cx, cy - 18, name, 30, 800, col["text"], "middle")
                   + text(cx, cy + 20, core[0], 20, 500, INK, "middle")
                   + text(cx, cy + 46, core[1], 20, 500, INK, "middle") + "</g>")
        out.append("</g>")
        centres.append((cx, cy))
    out.append('<g class="hot hub" data-key="system">' + hub_disc(hx, hy, hub_r) + hub_label(hx, hy, 38) + "</g>")
    reach = radius + proc_size * 0.72 + 12
    x0, x1 = min(c[0] for c in centres) - reach, max(c[0] for c in centres) + reach
    y0, y1 = min(c[1] for c in centres) - reach, max(c[1] for c in centres) + reach
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}">'
            + svg_defs("".join(defs)) + "".join(out) + "</svg>")


def valence():
    w, h = 1800, 960
    defs, out = [], []
    out.append(text(90, 66, "VALENCE: HOW MANY CONTINUOUS LOOPS ARE BONDED TO ONE SYSTEM", 15, 700, MUTED, ls=2.5))
    out.append(text(90, 126, "From monovalent Dev to bivalent DevOps to trivalent DevIntOps", 46, 800, INK))
    hy, r, width, dist, gap_start, gap_tip, hub_r = 430, 92, 38, 140, 8, 10, 39
    panels = [
        (300, 101, [("dev", 180, -1)], "MONOVALENT", "Dev", "We build it."),
        (900, 0, [("dev", 180, -1), ("ops", 0, 1)], "BIVALENT", "DevOps", "We build it and run it."),
        (1500, 0, [("dev", 210, -1), ("ops", 330, 1), ("int", 90, 1)], "TRIVALENT", "DevIntOps",
         "We build it, run it, and it learns how to decide."),
    ]
    names = {"dev": "Dev", "ops": "Ops", "int": "Int"}
    for pi, (px, shift, lobes, kind, name, tagline) in enumerate(panels):
        hx = px + shift
        rings = {}
        for key, theta, direction in lobes:
            rings[key] = ring_loop(defs, out, f"v{pi}{key}", key, (hx, hy), theta, dist, r, width,
                                   direction, 15, gap_start, gap_tip, gap=5)
            out.append(text(rings[key]["cx"], rings[key]["cy"] + 8, names[key], 23, 800, LOOPS[key]["text"], "middle"))
        out.append(hub_disc(hx, hy, hub_r))
        out.append(hub_label(hx, hy, 13))
        out.append(text(px, 744, kind, 15, 700, MUTED, "middle", 3))
        out.append(text(px, 792, name, 40, 800, INK, "middle"))
        out.append(text(px, 830, tagline, 20, 400, BODY, "middle"))
    for x, add, key in [(549, "+ Ops", "ops"), (1209, "+ Int", "int")]:
        out.append(f'<path d="M {x - 24} {hy} L {x + 22} {hy} M {x + 10} {hy - 12} L {x + 22} {hy} L {x + 10} {hy + 12}" '
                   f'stroke="#9CA3AF" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(text(x, hy - 26, add, 18, 800, LOOPS[key]["text"], "middle"))
    out.append(f'<line x1="90" y1="876" x2="1710" y2="876" stroke="{RULE}" stroke-width="2"/>')
    out.append(verbs(w / 2, 922, 20, full=False))
    out.append(text(w - 90, 66, CREDIT, 14, 500, MUTED, "end"))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


def bonds():
    w, h = 1600, 900
    defs, out = [], []
    out.append(text(80, 66, "PERSISTENT LEARNING BONDS: FROM LOCAL RETRY TO CROSS-STAGE MEMORY", 15, 700, MUTED, ls=2.5))
    out.append(text(80, 124, "Two bonds make a chain. Three make a network.", 44, 800, INK))
    out.append(text(80, 168, "A retry loop converges one task. A learning loop makes the next task start better.", 22, 400, BODY))
    out.append(f'<line x1="800" y1="222" x2="800" y2="830" stroke="{RULE}" stroke-width="2"/>')

    y, width, gap = 455, 54, 6
    head = width * 0.42
    keys = ["dev", "dev", "dev", "dev", "ops", "ops"]
    names = ["Spec", "Code", "Review", "Validate", "Release", "Operate"]

    def pipeline(uid, x0, x1, retry_opacity):
        track = Track([(x0, y), (x1 + 80, y)])
        seg = (x1 - x0 - gap * 5 - head) / 6
        spans = [(k * (seg + gap), k * (seg + gap) + seg) for k in range(6)]
        ribbon_segments(defs, out, track, spans, keys, names, width, head, uid, 16)
        centres = [x0 + (a + b) / 2 + head / 2 for a, b in spans]
        a, b, top, lift = centres[3], centres[1], y - width / 2 - 8, 96
        out.append(f'<g opacity="{retry_opacity}">'
                   f'<path d="M {a:.1f} {top} C {a:.1f} {top - lift} {b:.1f} {top - lift} {b:.1f} {top - 4}" fill="none" '
                   f'stroke="{AMBER}" stroke-width="2.5" stroke-dasharray="7 6"/>'
                   f'<path d="M {b - 7:.1f} {top - 12} L {b:.1f} {top} L {b + 7:.1f} {top - 12} Z" fill="{AMBER}"/>'
                   + text((a + b) / 2, top - lift * 0.75 - 14, "fail → retry until it passes", 15, 700, AMBER, "middle")
                   + "</g>")
        return centres

    out.append(text(80, 252, "AN AGENTIC PIPELINE TODAY, SIMPLIFIED", 15, 700, MUTED, ls=2.5))
    out.append(text(80, 290, "An agent in every box", 28, 800, INK))
    lc = pipeline("L", 90, 740, 1.0)
    a, b, bottom, drop = lc[5], lc[0], y + width / 2 + 10, 120
    out.append(f'<path d="M {a:.1f} {bottom} C {a:.1f} {bottom + drop} {b:.1f} {bottom + drop} {b:.1f} {bottom + 4}" '
               f'fill="none" stroke="#9CA3AF" stroke-width="2.5" stroke-dasharray="2 7" stroke-linecap="round"/>')
    out.append(f'<path d="M {b - 7:.1f} {bottom + 14} L {b:.1f} {bottom + 2} L {b + 7:.1f} {bottom + 14} Z" fill="#9CA3AF"/>')
    out.append(text((a + b) / 2, bottom + drop * 0.75 + 30, "production learning → next spec", 15, 700, MUTED, "middle"))
    out.append(text(80, 782, "Stages bond only to their neighbors.", 20, 400, BODY))
    out.append(text(80, 814, "Lessons wait for the next spec.", 20, 800, INK))

    out.append(text(860, 252, "THE SAME PIPELINE, PLUS INTELLIGENCE", 15, 700, MUTED, ls=2.5))
    out.append(text(860, 290, "Plus a third bond to shared memory", 28, 800, INK))
    sx0, sx1, sy0, sy1, sw = 935, 1470, 585, 705, 42
    rc = (sy1 - sy0) / 2
    pts = [(sx0 + (sx1 - sx0) * k / 200, sy0) for k in range(201)]
    pts += circle_pts(sx1, sy0 + rc, rc, -90, 180, 120)[1:]
    pts += [(sx1 - (sx1 - sx0) * k / 200, sy1) for k in range(1, 201)]
    pts += circle_pts(sx0, sy0 + rc, rc, 90, 180, 120)[1:-1]
    loop = Track(pts, closed=True)
    straight, cap, g = sx1 - sx0, math.pi * rc, 7
    cuts = [0, straight * 0.5, straight + cap, straight + cap + straight * 0.5, loop.length]
    spans = [(cuts[k], cuts[k + 1] - g) for k in range(4)]
    for x in pipeline("R", 880, 1530, 0.35):
        out.append(f'<line x1="{x:.1f}" y1="{y + width / 2 + 2}" x2="{x:.1f}" y2="{sy0 - sw / 2 - 2}" '
                   f'stroke="{LOOPS["int"]["dark"]}" stroke-width="3"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{sy0 - sw / 2 - 2}" r="5" fill="{LOOPS["int"]["dark"]}"/>')
    ribbon_segments(defs, out, loop, spans, ["int"] * 4, STAGES["int"], sw, sw * 0.42, "S", 15)
    out.append(text((sx0 + sx1) / 2, sy0 + rc + 7, "Intelligence · memory & judgment", 19, 800, LOOPS["int"]["text"], "middle"))
    out.append(text(860, 782, "Every stage also bonds to a shared memory.", 20, 400, BODY))
    out.append(text(860, 814, "Lessons reach the stage that needs them.", 20, 800, INK))
    out.append(verbs(w / 2, 876, 19, full=False))
    out.append(text(w - 80, 66, CREDIT, 14, 500, MUTED, "end"))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


def og_card():
    """1200x630 social preview card."""
    w, h = 1200, 630
    defs, out = [], []
    hx, hy = 905, 290
    for key, theta, direction in (("dev", 210, -1), ("ops", 330, 1), ("int", 90, 1)):
        ring = ring_loop(defs, out, f"og{key}", key, (hx, hy), theta, 128, 86, 34, direction, 12.5, 8, 10, gap=5)
        out.append(text(ring["cx"], ring["cy"] + 8, {"dev": "Dev", "ops": "Ops", "int": "Int"}[key], 22, 800,
                        LOOPS[key]["text"], "middle"))
    out.append(hub_disc(hx, hy, 34))
    out.append(hub_label(hx, hy, 12))
    out.append(text(68, 170, "DevIntOps", 104, 800, INK))
    out.append(text(72, 236, "From monovalent Dev to bivalent DevOps", 30, 700, INK))
    out.append(text(72, 274, "to trivalent DevIntOps", 30, 700, INK))
    out.append(text(72, 334, "Intelligence as the third continuous loop", 25, 400, BODY))
    out.append(text(72, 368, "in software engineering.", 25, 400, BODY))
    out.append(text(72, 424, "Pavel Chertorogov  ·  DRAFT  ·  18 October 2026", 18, 600, MUTED))
    out.append(rich(72, 492, [("Dev", LOOPS["dev"]["text"], 800), (" changes the implementation", BODY, 400)], 20, "start"))
    out.append(rich(72, 524, [("Ops", LOOPS["ops"]["text"], 800), (" changes how it runs", BODY, 400)], 20, "start"))
    out.append(rich(72, 556, [("Int", LOOPS["int"]["text"], 800), (" changes how it decides", BODY, 400)], 20, "start"))
    out.append(text(w - 60, h - 40, "devintops.org", 24, 800, LOOPS["dev"]["text"], "end"))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


if __name__ == "__main__":
    for name, fn in [("01-valence", valence), ("02-three-loops", three_loops), ("03-third-bond", bonds)]:
        (ASSETS / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print(f"wrote site/assets/diagrams/{name}.svg")
    (ASSETS.parent / "og-image.svg").write_text(og_card(), encoding="utf-8")
    print("wrote site/assets/og-image.svg")
    model = ASSETS.parent / "model"
    model.mkdir(exist_ok=True)
    (model / "three-loops.svg").write_text(three_loops_interactive(), encoding="utf-8")
    print("wrote site/assets/model/three-loops.svg")
