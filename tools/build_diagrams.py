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
    out.append(text(80, 124, "Two bonds make chains and rings. A third lets them branch.", 44, 800, INK))
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
    out.append(text((sx0 + sx1) / 2, sy0 + rc + 7, "Intelligence · memory and judgment", 19, 800, LOOPS["int"]["text"], "middle"))
    out.append(text(860, 782, "Every stage also bonds to a shared memory.", 20, 400, BODY))
    out.append(text(860, 814, "Lessons reach the stage that needs them.", 20, 800, INK))
    out.append(verbs(w / 2, 876, 19, full=False))
    out.append(text(w - 80, 66, CREDIT, 14, 500, MUTED, "end"))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


# Figure 5 (#lesson): how much evidence buys how much authority.
FA_GRAY = "#9CA3AF"


def _fa_open_arrow(x0, y0, x1, y1, stroke=FA_GRAY, width=2.5, size=9, dash=None):
    """Connector with an open arrowhead at (x1, y1)."""
    d = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / d, (y1 - y0) / d
    ax, ay = x1 - ux * size - uy * size * 0.8, y1 - uy * size + ux * size * 0.8
    bx, by = x1 - ux * size + uy * size * 0.8, y1 - uy * size - ux * size * 0.8
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="M {x0:.1f} {y0:.1f} L {x1:.1f} {y1:.1f}" stroke="{stroke}" stroke-width="{width}" fill="none" '
            f'stroke-linecap="round"{extra}/>'
            f'<path d="M {ax:.1f} {ay:.1f} L {x1:.1f} {y1:.1f} L {bx:.1f} {by:.1f}" stroke="{stroke}" stroke-width="{width}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def fig_evidence():
    w, h = 1600, 900
    defs, out = [], []
    ink, body, muted, amber = INK, BODY, MUTED, AMBER

    # Header
    out.append(text(80, 66, "HOW A LESSON MOVES: EVIDENCE BUYS AUTHORITY", 15, 700, muted, ls=2.5))
    out.append(text(80, 124, "How much evidence buys how much authority", 44, 800, ink))
    out.append(text(80, 168, "A lesson claims only what the highest level it has passed supports.", 22, 400, body))
    out.append(text(w - 80, 66, CREDIT, 14, 500, muted, "end"))

    # The evidence row: Candidate, then four levels
    yr, rw, gap = 352, 66, 7
    head = rw * 0.42
    x0, seg = 250, 260
    track = Track([(x0, yr), (x0 + 4 * seg + 3 * gap + head + 10, yr)])
    spans = [(k * (seg + gap), k * (seg + gap) + seg) for k in range(4)]
    levels = ["Replay", "Generalization", "Controlled exposure", "Observed outcome"]
    ribbon_segments(defs, out, track, spans, ["int"] * 4, levels, rw, head, "fa", 22)
    centres = [x0 + (a + b) / 2 + head / 2 for a, b in spans]
    x_tip = x0 + spans[-1][1] + head
    x_live = x0 + spans[1][1] + head / 2 + gap / 2

    chip_w = 126
    chip_x1 = 80 + chip_w
    out.append(f'<rect x="80" y="{yr - 24}" width="{chip_w}" height="48" rx="3" fill="#F8FAFC" stroke="{FA_GRAY}" stroke-width="1.5"/>')
    out.append(text(80 + chip_w / 2, yr + 7, "Candidate", 20, 700, ink, "middle"))
    out.append(_fa_open_arrow(chip_x1 + 8, yr, x0 - 8, yr))

    descriptions = [
        ("The original case now", "behaves as intended"),
        ("Cases it was not written from,", "kept out of its drafter's reach"),
        ("Shadow mode, a suggestion,", "a canary or a bounded slice"),
        ("A fixed window and comparable", "exposure, against a baseline"),
    ]
    for cx, (l1, l2) in zip(centres, descriptions):
        out.append(text(cx, yr + rw / 2 + 34, l1, 18, 400, body, "middle"))
        out.append(text(cx, yr + rw / 2 + 58, l2, 18, 400, body, "middle"))

    # Any level can count against a lesson: amber returns to the exit
    y_rail, r = 262, 12
    top = yr - rw / 2 - 8
    tip_x = 80 + 136 + 14  # "Revise or retire" is 136 wide at 19/700
    out.append(text(80, y_rail + 6.5, "Revise or retire", 19, 700, amber))
    for cx in centres:
        out.append(f'<path d="M {cx:.1f} {top:.1f} L {cx:.1f} {y_rail + r} Q {cx:.1f} {y_rail} {cx - r:.1f} {y_rail}" '
                   f'fill="none" stroke="{amber}" stroke-width="2.5" stroke-dasharray="7 6"/>')
    out.append(f'<path d="M {centres[-1] - r:.1f} {y_rail} L {tip_x + 10:.1f} {y_rail}" fill="none" stroke="{amber}" '
               f'stroke-width="2.5" stroke-dasharray="7 6"/>')
    out.append(f'<path d="M {tip_x + 12:.1f} {y_rail - 7} L {tip_x:.1f} {y_rail} L {tip_x + 12:.1f} {y_rail + 7} Z" fill="{amber}"/>')
    out.append(text((centres[0] + centres[-1]) / 2, y_rail - 16, "Any level can count against a lesson", 18, 700, amber, "middle"))

    # Live is not proven: the open check over the live levels
    y_ob = yr + rw / 2 + 92
    out.append(f'<path d="M {x_live:.1f} {y_ob - 8} L {x_live:.1f} {y_ob} L {x_tip:.1f} {y_ob} L {x_tip:.1f} {y_ob - 8}" '
               f'fill="none" stroke="{FA_GRAY}" stroke-width="2.5" stroke-dasharray="2 7" stroke-linecap="round"/>')
    out.append(rich((x_live + x_tip) / 2, y_ob + 28, [("Live is not proven:", ink, 700),
                                                        (" the check stays open until its date", body, 400)], 18))

    # Dispositions at the check date
    xd = 1400
    disp = [(yr - 72, "Keep"), (yr - 24, "Revise"), (yr + 24, "Retire")]
    for y, name in disp:
        out.append(_fa_open_arrow(x_tip + 10, yr, xd - 12, y - 6, size=8, width=2))
        out.append(text(xd, y, name, 19, 700, ink))
    out.append(_fa_open_arrow(x_tip + 10, yr, xd - 12, yr + 66, size=8, width=2, dash="2 6"))
    out.append(text(xd, yr + 72, "Can't tell:", 19, 700, ink))
    out.append(text(xd, yr + 96, "extend once,", 18, 400, body))
    out.append(text(xd, yr + 120, "then expire", 18, 400, body))

    # Authority band: what the lesson may do, widening with the evidence above it
    ybc = 622
    xb0, xb1, t0, t1 = x0, x_tip, 8, 66
    defs.append(f'<linearGradient id="faband" gradientUnits="userSpaceOnUse" x1="{xb0}" y1="0" x2="{xb1:.1f}" y2="0">'
                f'<stop offset="0" stop-color="#E5E7EB"/><stop offset="1" stop-color="#8B93A1"/></linearGradient>')
    out.append(f'<path d="M {xb0} {ybc - t0 / 2} L {xb1:.1f} {ybc - t1 / 2} L {xb1:.1f} {ybc + t1 / 2} L {xb0} {ybc + t0 / 2} Z" '
               f'fill="url(#faband)"/>')
    out.append(text(xb0 - 14, ybc + 7, "Draft", 19, 700, ink, "end"))
    out.append(text(xb1 + 16, ybc - 4, "Blocks or acts", 19, 700, ink))
    out.append(text(xb1 + 16, ybc + 20, "on its own", 19, 700, ink))
    # The go-live pin, flagged with who turns it on
    tag_w, tag_y = 222, ybc - 84
    out.append(f'<rect x="{x_live:.1f}" y="{tag_y}" width="{tag_w}" height="30" rx="3" fill="#F8FAFC" '
               f'stroke="{FA_GRAY}" stroke-width="1.5"/>')
    out.append(f'<line x1="{x_live:.1f}" y1="{tag_y}" x2="{x_live:.1f}" y2="{ybc + 36}" stroke="{ink}" stroke-width="2" '
               f'stroke-linecap="round"/>')
    out.append(text(x_live + tag_w / 2 + 1, tag_y + 21, "Only the owner turns it on", 17, 600, ink, "middle"))
    out.append(text(x_live - 12, ybc + 60, "A comment a reviewer can dismiss", 18, 400, body, "end"))
    out.append(text(x_live - 12, ybc + 84, "may go live", 18, 700, ink, "end"))
    out.append(text(xb1, ybc + 60, "A rule that blocks merges", 18, 400, body, "end"))
    out.append(text(xb1, ybc + 84, "runs without blocking first", 18, 700, ink, "end"))
    out.append(text(80, ybc + 154, "The more it can block or act on its own, the higher it must get first.", 20, 800, ink))

    out.append(f'<line x1="80" y1="{h - 74}" x2="{w - 80}" y2="{h - 74}" stroke="{RULE}" stroke-width="2"/>')
    out.append(verbs(w / 2, h - 30, 19, full=False))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


# Figure 4 (#applications): one model, two applications.
#
# The same three loops run around the engineering system and around the product system. Each keeps its own owner,
# memory and permissions; the engineering system builds and runs the product; no lesson crosses between the two
# memories unless both owners allow it.
FB_W, FB_H = 1600, 1000
FB_K = 1600 / 1800  # valence()'s trivalent panel, kept at the same share of a 1600-wide canvas as of its 1800-wide one
FB_TREFOIL = dict(dist=140 * FB_K, r=92 * FB_K, width=38 * FB_K, gap_start=8, gap_tip=10, gap=5, hub_r=round(39 * FB_K))
FB_LOBES = (("dev", 210, -1), ("ops", 330, 1), ("int", 90, 1))
FB_NAMES = {"dev": "Dev", "ops": "Ops", "int": "Int"}
FB_CONNECTOR = "#9CA3AF"


def _fb_trefoil(defs, out, uid, hx, hy):
    """Three ring loops around a dark System hub, without stage names (too small to carry white labels here)."""
    t = FB_TREFOIL
    rings = {}
    for key, theta, direction in FB_LOBES:
        scratch = []
        rings[key] = ring_loop(defs, scratch, f"{uid}{key}", key, (hx, hy), theta, t["dist"], t["r"], t["width"],
                                  direction, 15, t["gap_start"], t["gap_tip"], gap=t["gap"])
        out.extend(e for e in scratch if "<textPath" not in e)
        out.append(text(rings[key]["cx"], rings[key]["cy"] + 7, FB_NAMES[key], 21, 800, LOOPS[key]["text"], "middle"))
    out.append(hub_disc(hx, hy, t["hub_r"]))
    out.append(hub_label(hx, hy, 13))
    return rings


def _fb_store(out, x, y, w, h, title, lines):
    out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="3" fill="#F8FAFC" stroke="{RULE}" stroke-width="2"/>')
    out.append(text(x + 22, y + 35, title, 20, 800, INK))
    for k, line in enumerate(lines):
        out.append(text(x + 22, y + 66 + k * 27, line, 20, 400, BODY))


def _fb_bond(out, x0, y0, x1, y1):
    dark = LOOPS["int"]["dark"]
    out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{dark}" stroke-width="3"/>')
    out.append(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="5" fill="{dark}"/>')


def _fb_rows(out, x, y, rows, label_w=140, step=36, line=26):
    """Label/value rows; a value given as a tuple wraps onto one line per item."""
    for label, fill, value in rows:
        parts = value if isinstance(value, tuple) else (value,)
        out.append(text(x, y, label, 19, 700, fill))
        for k, part in enumerate(parts):
            out.append(text(x + label_w, y + k * line, part, 20, 400, INK))
        y += step + (len(parts) - 1) * line


def fig_applications():
    w, h = FB_W, FB_H
    defs, out = [], []
    out.append(text(80, 66, "ONE MODEL, TWO APPLICATIONS", 15, 700, MUTED, ls=2.5))
    out.append(text(80, 124, "The same pattern, separate permission scopes", 44, 800, INK))
    out.append(text(80, 168, "Its triggers, actions and clocks can differ.", 22, 400, BODY))
    out.append(text(w - 80, 66, CREDIT, 14, 500, MUTED, "end"))

    reach = FB_TREFOIL["dist"] * 0.866 + FB_TREFOIL["r"] + FB_TREFOIL["width"] / 2  # hub to a trefoil's outer side
    top = FB_TREFOIL["dist"] / 2 + FB_TREFOIL["r"] + FB_TREFOIL["width"] / 2  # hub to the trefoil's top
    hy = round(294 + top)
    lx, rx = 80, 1050  # text columns; the right one is as far left as its widest line needs
    lh = round((w + lx - rx) / 2)  # each trefoil sits equally far in from its text column
    rh = w - lh  # mirrored about the middle
    mid = (lh + rh) / 2

    out.append(text(lx, 228, "ENGINEERING SYSTEM", 15, 700, MUTED, ls=2.5))
    out.append(text(lx, 266, "How we build and run software", 28, 800, INK))
    out.append(text(rx, 228, "PRODUCT SYSTEM", 15, 700, MUTED, ls=2.5))
    out.append(text(rx, 266, "What we build: the running product", 28, 800, INK))

    left = _fb_trefoil(defs, out, "fbE", lh, hy)
    right = _fb_trefoil(defs, out, "fbP", rh, hy)

    # builds and runs: a plain move from one system to the other, above the memories
    ax0, ax1 = lh + reach - 8, rh - reach + 8
    out.append(f'<path d="M {ax0:.1f} {hy} L {ax1:.1f} {hy} M {ax1 - 12:.1f} {hy - 12} L {ax1:.1f} {hy} L {ax1 - 12:.1f} {hy + 12}" '
               f'stroke="{FB_CONNECTOR}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append(text(mid, hy - 16, "builds and runs", 19, 700, MUTED, "middle"))

    # two separate memories, each bonded to its own Intelligence loop, with a barrier between them. The bonds run a
    # little above the ring centres, so on both rings they meet the ribbon mid-segment rather than at a chevron joint.
    ring_out, lift = FB_TREFOIL["r"] + FB_TREFOIL["width"] / 2, 22
    by = left["int"]["cy"] - lift
    bx = (ring_out ** 2 - lift ** 2) ** 0.5 - 1  # where a bond at that height leaves the ring, from its centre
    sw, sh, gap = 280, 110, 34
    sy = by - sh / 2
    lsx, rsx = mid - gap - sw, mid + gap
    _fb_store(out, lsx, sy, sw, sh, "Engineering memory", ["lesson records and", "their evidence"])
    _fb_store(out, rsx, sy, sw, sh, "Product memory", ["preferences and", "decision policies"])
    _fb_bond(out, left["int"]["cx"] + bx, by, lsx, by)
    _fb_bond(out, right["int"]["cx"] - bx, by, rsx + sw, by)
    out.append(f'<line x1="{mid}" y1="{sy - 12:.1f}" x2="{mid}" y2="{sy + sh + 12:.1f}" stroke="{INK}" stroke-width="8"/>')
    out.append(text(mid, sy + sh + 46, "No lesson crosses", 20, 700, INK, "middle"))
    out.append(text(mid, sy + sh + 72, "unless both owners allow it", 20, 400, BODY, "middle"))

    ry = 756
    _fb_rows(out, lx, ry, [("Owner", MUTED, "a named team"),
                        ("Feedback", MUTED, "later outcomes in the targeted class"),
                        ("Intelligence", LOOPS["int"]["text"], "changes next time's default"),
                        ("Stage owners", MUTED, "can veto writes to their stage")])
    _fb_rows(out, rx, ry, [("Owner", MUTED, "the product owner sets the limits"),
                        ("Feedback", MUTED, "what the user says about it"),
                        ("Intelligence", LOOPS["int"]["text"], "also makes this run's decision"),
                        ("Users", MUTED, ("can see and delete what", "the product learned about them"))])

    out.append(f'<line x1="80" y1="932" x2="{w - 80}" y2="932" stroke="{RULE}" stroke-width="2"/>')
    out.append(verbs(w / 2, h - 30, 19, full=False))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


# Figure 7 (#falsification): the randomized shadow test.
FD_W, FD_H = 1600, 860
FD_LINE = "#9CA3AF"   # connector gray
FD_CARD = "#F8FAFC"   # light card fill
FD_TILE = "#9CA3AF"   # a class: neutral gray


def _fd_card(x, y, w, h):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" fill="{FD_CARD}" '
            f'stroke="{RULE}" stroke-width="2"/>')


def _fd_arrow(x0, y0, x1, y1):
    """Straight connector with an open arrowhead: a move."""
    d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    ux, uy = (x1 - x0) / d, (y1 - y0) / d
    lx, ly = x1 - ux * 11 - uy * 9, y1 - uy * 11 + ux * 9
    rx, ry = x1 - ux * 11 + uy * 9, y1 - uy * 11 - ux * 9
    return (f'<path d="M {x0:.1f} {y0:.1f} L {x1:.1f} {y1:.1f} M {lx:.1f} {ly:.1f} L {x1:.1f} {y1:.1f} L {rx:.1f} {ry:.1f}" '
            f'fill="none" stroke="{FD_LINE}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')


def _fd_list_card(x, y, w, h, head, rows, gap=16):
    """A card with a two-line head and a list of short phrases divided by thin rules."""
    out = [_fd_card(x, y, w, h)]
    out += [text(x + 24, y + 44 + 30 * k, s, 24, 800, INK) for k, s in enumerate(head)]
    ty = y + 124
    for k, lines in enumerate(rows):
        if k:
            out.append(f'<line x1="{x + 24}" y1="{ty - 23 - gap / 2:.1f}" x2="{x + w - 24}" y2="{ty - 23 - gap / 2:.1f}" '
                       f'stroke="{RULE}" stroke-width="2"/>')
        out += [text(x + 24, ty + 27 * j, s, 20, 400, BODY) for j, s in enumerate(lines)]
        ty += 27 * len(lines) + gap
    return "".join(out)


def fig_shadow():
    defs, out = [], []
    out.append(text(80, 66, "HOW THIS COULD BE WRONG", 15, 700, MUTED, ls=2.5))
    out.append(text(80, 124, "One half live, one in shadow, the same checks", 44, 800, INK))
    out.append(text(80, 168, "Someone outside the loop draws the halves.", 22, 400, BODY))
    out.append(text(FD_W - 80, 66, CREDIT, 14, 500, MUTED, "end"))

    live_y, shad_y = 340, 550            # lane centre lines
    mid_y = (live_y + shad_y) / 2
    rib_w = 56
    head = rib_w * 0.42
    x0 = 380                             # left edge shared by the draw, the tiles, the lane heads and the band
    rx0, rx1 = 672, 1170                 # ribbon run; heads end at rx1 + head
    end = rx1 + head
    card_h = 356

    # Left: everything fixed before starting.
    fx, fw = 80, 236
    out.append(_fd_list_card(fx, mid_y - card_h / 2, fw, card_h, ("Before starting,", "freeze"), [
        ("the class list",), ("the scoring",), ("the guardrails",),
        ("the smallest gain", "worth having"), ("one primary outcome",)]))

    # The draw, made outside the loop: each eligible class goes, whole, into one half.
    bw, bh = 280, 92
    bx = x0 + bw / 2
    out.append(_fd_arrow(fx + fw + 10, mid_y, x0 - 10, mid_y))
    out.append(_fd_card(x0, mid_y - bh / 2, bw, bh))
    out.append(text(bx, mid_y - 17.5, "Someone outside the loop", 20, 800, INK, "middle"))
    out.append(text(bx, mid_y + 8.5, "draws the eligible low-risk", 18, 400, BODY, "middle"))
    out.append(text(bx, mid_y + 31.5, "classes at random", 18, 400, BODY, "middle"))

    tile_h, tile_gap = 40, 6

    def tiles(y, widths):
        x = x0
        for wdt in widths:
            out.append(f'<rect x="{x:.1f}" y="{y - tile_h / 2:.1f}" width="{wdt}" height="{tile_h}" rx="2" fill="{FD_TILE}"/>')
            x += wdt + tile_gap

    # Classes differ in size, so the two rows differ in length: the halves need not match in exposure.
    tiles(live_y, [30, 52, 22, 40, 26, 44])
    tiles(shad_y, [46, 22, 34, 60, 18, 40])
    out.append(_fd_arrow(bx, mid_y - bh / 2 - 8, bx, live_y + tile_h / 2 + 8))
    out.append(_fd_arrow(bx, mid_y + bh / 2 + 8, bx, shad_y - tile_h / 2 - 8))

    # The lessons of each half: live at full strength, shadow faded.
    n, g = 4, 7
    seg = (rx1 - rx0 - g * (n - 1) - head) / n
    spans = [(k * (seg + g), k * (seg + g) + seg) for k in range(n)]
    for uid, y, opacity in (("fdL", live_y, 1.0), ("fdS", shad_y, 0.32)):
        track = Track([(rx0, y), (rx1 + 80, y)])
        ribbon_segments(defs, out, track, spans, ["int"] * n, [None] * n, rib_w, head, uid, 22, opacity=opacity)

    out.append(text(x0, live_y - 88, "Live half", 28, 800, INK))
    out.append(text(x0, live_y - 58, "lessons apply", 20, 400, BODY))
    out.append(text(x0, shad_y + 78, "Shadow half", 28, 800, INK))
    out.append(text(x0, shad_y + 108, "lessons record what they would have done and change nothing", 20, 400, BODY))

    # Amber stop across the live lane.
    s0, s1 = spans[2]
    sx = rx0 + (s0 + s1 + head) / 2
    bar = (f'x1="{sx:.1f}" y1="{live_y - rib_w / 2 - 11:.1f}" x2="{sx:.1f}" y2="{live_y + rib_w / 2 + 11:.1f}" '
           f'stroke-linecap="round"')
    out.append(f'<line {bar} stroke="#FFFFFF" stroke-width="14"/><line {bar} stroke="{AMBER}" stroke-width="6"/>')
    out.append(text(sx, live_y - 88, "Stop the live half if a guardrail breaks", 19, 700, AMBER, "middle"))
    out.append(text(sx, live_y - 58, "don't stop early because the numbers look good", 18, 400, MUTED, "middle"))

    # Dotted spillover: a lesson that reaches the other half is logged.
    s0, s1 = spans[1]
    px = rx0 + (s0 + s1 + head) / 2
    top, bot = live_y + rib_w / 2 + 10, shad_y - rib_w / 2 - 8
    qx = px + 44
    out.append(f'<path d="M {px:.1f} {top:.1f} C {px:.1f} {mid_y:.1f} {qx:.1f} {mid_y - 20:.1f} {qx:.1f} {bot - 6:.1f}" '
               f'fill="none" stroke="{FD_LINE}" stroke-width="2.5" stroke-dasharray="2 7" stroke-linecap="round"/>')
    out.append(f'<path d="M {qx - 7:.1f} {bot - 12:.1f} L {qx:.1f} {bot:.1f} L {qx + 7:.1f} {bot - 12:.1f} Z" fill="{FD_LINE}"/>')
    out.append(text(qx + 22, mid_y - 3, "Log any lesson that", 18, 700, MUTED))
    out.append(text(qx + 22, mid_y + 21, "reaches the other half", 18, 700, MUTED))

    # Both halves keep the protections they already have.
    by, bhh = shad_y + 134, 46
    out.append(f'<rect x="{x0}" y="{by}" width="{end - x0:.1f}" height="{bhh}" rx="3" fill="{RULE}"/>')
    out.append(rich((x0 + end) / 2, by + bhh / 2 + 7, [
        ("Existing practices and protections in both halves", INK, 700),
        ("  \u00b7  never hold back a known safety fix", BODY, 400)], 19))

    # Right: the same checks on both halves, judged by the unit that was split.
    cx0, cw = 1250, 270
    for y in (live_y, shad_y):
        out.append(_fd_arrow(end + 10, y, cx0 - 10, y))
    out.append(_fd_list_card(cx0, mid_y - card_h / 2, cw, card_h, ("Compare,", "by the unit you split"), [
        ("the primary outcome",), ("flow",), ("how many expected", "effects came true"),
        ("the full cost of learning,", "rejected drafts included")], gap=16 + 16 / 3))

    out.append(f'<line x1="80" y1="{FD_H - 76}" x2="{FD_W - 80}" y2="{FD_H - 76}" stroke="{RULE}" stroke-width="2"/>')
    out.append(verbs(FD_W / 2, FD_H - 30, 19, full=False))
    return svg_open(FD_W, FD_H, "".join(defs)) + "".join(out) + "</svg>"


# Figure 6 (#governance): what the loop may change, and what stays out of its reach.
FC_ZONE_FILLS = ("#FFFFFF", "#F3F4F6", RULE)  # innermost to outermost: darker the further from the loop


def _fc_lines(x, y, rows, size, weight, fill, lh):
    return "".join(text(x, y + k * lh, s, size, weight, fill) for k, s in enumerate(rows))


def _fc_rect(x0, y0, x1, y1, fill, rx=3):
    return f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="{rx}" fill="{fill}"/>'


def _fc_ring(defs, out, cx, cy, r, width, size):
    """A closed Intelligence loop: four chevron segments running clockwise from the top."""
    track = Track(circle_pts(cx, cy, r, -90, 360, 720)[:-1], closed=True)
    quarter = track.length / 4
    spans = [(k * quarter, (k + 1) * quarter - 7) for k in range(4)]
    ribbon_segments(defs, out, track, spans, ["int"] * 4, STAGES["int"], width, width * 0.42, "fcr", size,
                       centre=(cx, cy))
    out.append(text(cx, cy + 8, "Intelligence", 23, 800, LOOPS["int"]["text"], "middle"))


def fig_limits():
    w, h = 1600, 980
    defs, out = [], []
    out.append(text(80, 66, "OWNER, MEMORY AND LIMITS", 15, 700, MUTED, ls=2.5))
    out.append(text(80, 124, "A limit the loop can edit is only a suggestion", 44, 800, INK))
    out.append(text(80, 168, "People own goals, permissions and boundaries. The loop proposes and adapts inside them.",
                       22, 400, BODY))
    out.append(text(w - 80, 66, CREDIT, 14, 500, MUTED, "end"))

    # Three nested zones around the loop; each outer zone carries its label in a strip below the one inside it.
    x0, x1, y0, inset, strip, pad = 80, 1058, 238, 24, 106, 30
    ring_r, ring_w = 124, 52
    z1_top = y0 + 2 * inset
    z1_bot = z1_top + 2 * (ring_r + ring_w / 2 + pad)
    z2_bot = z1_bot + strip
    z3_bot = z2_bot + strip
    out.append(_fc_rect(x0, y0, x1, z3_bot, FC_ZONE_FILLS[2]))
    out.append(_fc_rect(x0 + inset, y0 + inset, x1 - inset, z2_bot, FC_ZONE_FILLS[1]))
    out.append(_fc_rect(x0 + 2 * inset, z1_top, x1 - 2 * inset, z1_bot, FC_ZONE_FILLS[0]))

    cx, cy = x0 + 2 * inset + pad + ring_r + ring_w / 2, (z1_top + z1_bot) / 2
    _fc_ring(defs, out, cx, cy, ring_r, ring_w, 22)

    def group(x, title, note, items):
        out.append(text(x, cy - 62, title, 28, 800, INK))
        out.append(text(x, cy - 26, note, 19, 400, BODY))
        out.append(_fc_lines(x, cy + 22, items, 20, 500, INK, 30))

    group(cx + ring_r + ring_w / 2 + 40, "Applies on its own", "if one step can undo it and a wrong one can do little harm",
          ["context in a narrow scope", "routing", "thresholds within an approved band"])

    sep = "   ·   "
    for top, title, items in (
            (z1_bot, "Needs a person's approval",
             ["blocking rules", "policy", "changes to how it reads outcomes, weighs options or drafts lessons"]),
            (z2_bot, "A person makes it",
             ["a merge", "a production configuration change", "a new model, through Development's gates"])):
        out.append(text(x0 + 2 * inset, top + 44, title, 28, 800, INK))
        out.append(text(x0 + 2 * inset, top + 80, sep.join(items), 20, 500, INK))

    # The wall stands apart from the zones, and the loop's own limits lie beyond it.
    wx, ww = x1 + 16, 36
    out.append(f'<rect x="{wx}" y="{y0 - 16}" width="{ww}" height="{z3_bot - y0 + 32}" fill="{INK}"/>')
    ox = wx + ww + 30
    group(ox, "Out of reach", "enforced outside the loop",
          ["its permissions, budget and stop switch", "the evidence rules", "the audit trail", "how it is scored"])
    out.append(_fc_lines(ox, z2_bot + 53, ["A stopped loop keeps recording", "outcomes and changes nothing."],
                      19, 400, BODY, 27))

    out.append(verbs(w / 2, h - 30, 19, full=False))
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
    out.append(text(72, 424, "Pavel Chertorogov  ·  Version 1.0  ·  19 October 2026", 18, 600, MUTED))
    out.append(rich(72, 492, [("Dev", LOOPS["dev"]["text"], 800), (" changes the implementation", BODY, 400)], 20, "start"))
    out.append(rich(72, 524, [("Ops", LOOPS["ops"]["text"], 800), (" changes how it runs", BODY, 400)], 20, "start"))
    out.append(rich(72, 556, [("Int", LOOPS["int"]["text"], 800), (" changes how it decides", BODY, 400)], 20, "start"))
    out.append(text(w - 60, h - 40, "devintops.org", 24, 800, LOOPS["dev"]["text"], "end"))
    return svg_open(w, h, "".join(defs)) + "".join(out) + "</svg>"


if __name__ == "__main__":
    for name, fn in [("01-valence", valence), ("02-three-loops", three_loops), ("03-third-bond", bonds),
                     ("04-applications", fig_applications), ("05-evidence", fig_evidence), ("06-limits", fig_limits),
                     ("07-shadow", fig_shadow)]:
        (ASSETS / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print(f"wrote site/assets/diagrams/{name}.svg")
    (ASSETS.parent / "og-image.svg").write_text(og_card(), encoding="utf-8")
    print("wrote site/assets/og-image.svg")
    model = ASSETS.parent / "model"
    model.mkdir(exist_ok=True)
    (model / "three-loops.svg").write_text(three_loops_interactive(), encoding="utf-8")
    print("wrote site/assets/model/three-loops.svg")
