// devintops.org model explorer. Makes the three-loops diagram explorable: every stage, continuous process,
// loop and the System hub explains itself on hover, click, tap or keyboard focus, and a walkthrough follows
// one escaped bug through the loops. Progressive enhancement: the static figure and the panel's resting text
// work without JavaScript, and print always shows the static figure. Content lives in assets/model-data.js.
(() => {
  "use strict";
  const M = window.DEVINTOPS_MODEL;
  if (!M) return;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const wideLayout = window.matchMedia("(min-width: 961px)");
  const LEVEL = { dev: 1, ops: 2, int: 3 };
  // Pointer timing. A part previews once the pointer rests on it for HOVER_INTENT ms, so a pointer passing
  // through on its way elsewhere changes nothing. Crossing the paper between parts keeps the preview for
  // LINGER ms; leaving the drawing lets go after LET_GO ms.
  const HOVER_INTENT = 60;
  const LINGER = 500;
  const LET_GO = 140;
  // Headings of the part view's "how" section, which is always shown.
  const HOW = {
    stage: "How it works: in, out, what to watch",
    process: "How it works",
    loop: "Unit of work, clock and metric",
    hub: "What each loop changes",
  };
  const PROCESS_OF = {};
  for (const [key, part] of Object.entries(M.parts)) {
    if (part.kind === "process") for (const stage of part.spans) PROCESS_OF[stage] = key;
  }
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const loopOf = (key) => (M.loops[key] ? key : (M.parts[key] && M.parts[key].loop) || null);

  document.querySelectorAll("[data-explorer]").forEach((root, n) => {
    fetch(root.dataset.src)
      .then((res) => (res.ok ? res.text() : Promise.reject(new Error(String(res.status)))))
      .then((markup) => setup(root, markup, n))
      .catch(() => {});
  });

  function setup(root, markup, n) {
    const art = root.querySelector(".explorer-art");
    const figure = root.querySelector(".explorer-figure");
    const panel = root.querySelector(".explorer-panel");
    const controls = root.querySelector(".explorer-controls");
    const parsed = document.createElement("template");
    parsed.innerHTML = markup.trim();
    const svg = parsed.content.querySelector("svg");
    if (!art || !figure || !panel || !controls || !svg) return;

    svg.classList.add("model");
    svg.setAttribute("role", "group");
    svg.setAttribute("aria-label", "Three loops around one system. Use the arrow keys to move between the parts.");
    // Chrome otherwise makes the svg root its own tab stop, ahead of the roving stop on the parts.
    svg.setAttribute("tabindex", "-1");
    svg.setAttribute("focusable", "false");
    art.append(svg); // the static figure stays in the DOM: CSS hides it while live and shows it in print

    const els = new Map();
    for (const el of svg.querySelectorAll(".hot")) {
      const key = el.dataset.key;
      if (!M.parts[key]) continue;
      els.set(key, el);
      el.setAttribute("role", "button");
      el.setAttribute("tabindex", key === "system" ? "0" : "-1");
      el.setAttribute("aria-label", nameOf(key));
    }

    const rest = panel.querySelector(".panel-body");
    const restHTML = rest ? rest.innerHTML : "";
    panel.hidden = false;
    panel.innerHTML = '<div class="panel-body"></div><p class="sr-only" aria-live="polite"></p>';
    const view = panel.querySelector(".panel-body");
    const live = panel.querySelector("[aria-live]");
    const labelId = `${root.id || `explorer-${n + 1}`}-valence`;
    controls.innerHTML =
      `<span class="valence-label" id="${labelId}">Compare one, two and three loops</span>` +
      `<div class="seg-control" role="group" aria-labelledby="${labelId}">` +
      ["Dev", "DevOps", "DevIntOps"].map((label, i) =>
        `<button type="button" data-valence="${i + 1}" aria-pressed="${i === 2}">${label}</button>`).join("") +
      "</div>";
    root.classList.add("is-live");

    const state = { mode: "intro", pinned: null, preview: null, valence: 3, step: 0, current: "system" };
    let clearTimer = 0;
    let hoverTimer = 0;
    let shown = null;
    let reservedWidth = 0;
    let kept = 0;
    let keptFrame = 0;
    const sizes = new Map(); // `${valence}:${key}` → the height a part view takes, from reserve()

    const shownValence = () => (state.mode === "tour" ? M.tour[state.step].valence : state.valence);
    const visible = (key) => {
      const loop = loopOf(key);
      return !loop || LEVEL[loop] <= shownValence();
    };

    function nameOf(key) {
      const p = M.parts[key];
      const loop = loopOf(key);
      if (p.kind === "stage") return `${p.title}, ${M.loops[loop].name} stage`;
      if (p.kind === "process") return `${p.title}, ${M.loops[loop].name}`;
      if (p.kind === "loop") return `${p.title} loop`;
      return "System, the hub of all three loops";
    }

    function litFor(key) {
      const p = M.parts[key];
      if (p.kind === "hub") return null;
      if (p.kind === "loop") return M.order.filter((k) => loopOf(k) === key);
      if (p.kind === "process") return [key, ...p.spans];
      return [key, PROCESS_OF[key]];
    }

    function relatedOf(key) {
      const p = M.parts[key];
      if (p.kind === "hub") return ["dev", "ops", "int"];
      if (p.kind === "loop") {
        return [...M.loops[key].stages, ...M.order.filter((k) => M.parts[k].kind === "process" && M.parts[k].loop === key)];
      }
      if (p.kind === "process") return [...p.spans, p.loop];
      return [p.loop, PROCESS_OF[key]];
    }

    function paint(lit, active) {
      svg.classList.toggle("has-focus", Boolean(lit));
      for (const [key, el] of els) {
        el.classList.toggle("is-lit", Boolean(lit) && lit.includes(key));
        el.classList.toggle("is-active", key === active);
        if (key === state.pinned && state.mode === "part") el.setAttribute("aria-current", "true");
        else el.removeAttribute("aria-current");
        if (visible(key)) el.removeAttribute("aria-hidden");
        else el.setAttribute("aria-hidden", "true");
      }
    }

    const chip = (key) => {
      const loop = loopOf(key);
      return `<button type="button" class="chip${loop ? ` ${loop}` : ""}" data-go="${key}">${esc(M.parts[key].title)}</button>`;
    };

    function metaOf(key) {
      const p = M.parts[key];
      const loop = loopOf(key);
      if (p.kind === "stage") return `${M.loops[loop].name} · stage ${M.loops[loop].stages.indexOf(key) + 1} of 4`;
      if (p.kind === "process") return `${M.loops[loop].name} · runs across ${M.parts[p.spans[0]].title} and ${M.parts[p.spans[1]].title}`;
      if (p.kind === "loop") return `Loop · ${M.loops[key].verb}`;
      return "The system in the middle";
    }

    function partView(key) {
      const p = M.parts[key];
      const loop = loopOf(key);
      const keys = M.order.filter(visible);
      const at = keys.indexOf(key);
      const prev = keys[(at - 1 + keys.length) % keys.length];
      const next = keys[(at + 1) % keys.length];
      const facts = (p.facts || []).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("");
      const related = relatedOf(key).filter(visible).map(chip).join(" ");
      const noteTint = loop === "dev" || loop === "ops" ? " is-int" : "";
      return `<div class="panel-main is-part"><h3 class="panel-title${loop ? ` ${loop}` : ""}" tabindex="-1">${esc(p.title)}${p.isNew ? ' <span class="tag">new</span>' : ""}</h3>
        <p class="panel-meta">${esc(metaOf(key))}</p>
        <p class="panel-summary">${esc(p.summary)}</p>
        ${p.note ? `<p class="panel-note${noteTint}"><strong>${esc(p.noteLabel)}.</strong> ${esc(p.note)}</p>` : ""}
        <div class="panel-how"><h4>${esc(HOW[p.kind])}</h4>
          <p>${esc(p.body)}</p>${facts ? `<dl class="panel-facts">${facts}</dl>` : ""}
        </div>
        ${related ? `<p class="panel-related"><span>Related</span> ${related}</p>` : ""}</div>
        <div class="panel-nav is-part">
          <button type="button" class="link-button" data-go="${prev}" data-nav="prev"><span aria-hidden="true">← </span>${esc(M.parts[prev].title)}</button>
          <button type="button" class="link-button" data-overview>Overview</button>
          <button type="button" class="link-button" data-go="${next}" data-nav="next">${esc(M.parts[next].title)}<span aria-hidden="true"> →</span></button>
        </div>`;
    }

    function introView() {
      return `${restHTML}
        <p class="panel-cta"><button type="button" class="button" data-tour-start>Follow one escaped bug</button></p>
        <p class="panel-hint">Select any part of the diagram to see what it does. On a keyboard, tab to the diagram and use the arrow keys; Escape comes back here.</p>`;
    }

    function valenceView() {
      const v = M.valence[state.valence];
      const add = state.valence < 3
        ? `<p class="panel-add"><button type="button" class="link-button" data-valence-go="${state.valence + 1}">Add the ${state.valence === 1 ? "Operations" : "Intelligence"} loop<span aria-hidden="true"> →</span></button></p>`
        : "";
      return `<div class="panel-main is-valence"><h3 class="panel-title" tabindex="-1">${esc(v.title)}</h3>
        <p class="panel-meta">${esc(v.tagline)}</p>
        <p class="panel-summary">${esc(v.text)}</p></div>
        ${add}
        <p class="panel-related"><span>Loops</span> ${["dev", "ops", "int"].filter(visible).map(chip).join(" ")}</p>`;
    }

    function tourView() {
      const step = M.tour[state.step];
      const last = state.step === M.tour.length - 1;
      // Steps 1 to 3 run in a bivalent system; the track shows where DevOps stops and the third loop takes over.
      const track = M.tour.map((s, i) =>
        `<span class="${s.valence === 2 ? "is-ops" : "is-int"}${i <= state.step ? " is-reached" : ""}"></span>`).join("");
      return `<div class="panel-main is-tour"><div class="tour-track" aria-hidden="true">${track}</div>
        <h3 class="panel-title" tabindex="-1">${esc(step.title)}</h3>
        <p class="panel-meta">One escaped bug · step ${state.step + 1} of ${M.tour.length}</p>
        <p class="panel-summary">${esc(step.text)}</p></div>
        <div class="panel-nav">
          <button type="button" class="link-button" data-tour="prev"${state.step === 0 ? " disabled" : ""}><span aria-hidden="true">← </span>Back</button>
          ${last
            ? '<button type="button" class="button" data-tour="exit">Explore on your own</button>'
            : '<button type="button" class="button" data-tour="next">Next<span aria-hidden="true"> →</span></button>'}
        </div>
        ${last ? "" : '<p class="panel-exit"><button type="button" class="link-button" data-tour="exit">Leave the walkthrough</button></p>'}`;
    }

    // Every view the panel can show is rendered once into a hidden copy at the current width. The panel reserves
    // the height of the tallest view it covers, and each kind of view (part, walkthrough step, valence) keeps its
    // navigation where its tallest covered member puts it, so moving among those views moves nothing. Side by
    // side it covers every view except an outlier: a part taller than the drawing and more than a fifth taller
    // than the median part (today the Intelligence loop), which makes the page longer while it is shown instead
    // of leaving a gap under the drawing for every other view. Stacked, parts keep their own height and only the
    // other views share one. Runs again when the panel's width changes.
    function reserve() {
      const width = panel.getBoundingClientRect().width;
      if (!width) return;
      reservedWidth = Math.round(width);
      const probe = document.createElement("aside");
      probe.className = panel.className;
      probe.setAttribute("aria-hidden", "true");
      probe.inert = true;
      probe.style.cssText = `position:absolute;top:0;left:-10000px;width:${width}px;visibility:hidden;pointer-events:none`;
      const body = probe.appendChild(document.createElement("div"));
      body.className = "panel-body";
      panel.after(probe);
      const saved = { mode: state.mode, valence: state.valence, step: state.step };
      const rows = [];
      const take = (kind, html, key) => {
        body.innerHTML = html;
        const main = body.querySelector(".panel-main");
        rows.push({ kind, key, valence: state.valence, total: body.getBoundingClientRect().height,
          main: main ? main.getBoundingClientRect().height : 0 });
      };
      try {
        state.mode = "intro";
        take("intro", introView());
        for (let v = 1; v <= 3; v++) {
          state.valence = v;
          state.mode = "valence";
          take("valence", valenceView());
          state.mode = "part";
          for (const key of M.order) if (visible(key)) take("part", partView(key), key);
        }
        state.mode = "tour";
        for (let i = 0; i < M.tour.length; i++) {
          state.step = i;
          take("tour", tourView());
        }
      } finally {
        Object.assign(state, saved);
        probe.remove();
      }
      const wide = wideLayout.matches;
      const parts = rows.filter((r) => r.kind === "part").map((r) => r.total).sort((a, b) => a - b);
      const median = parts[Math.floor(parts.length / 2)] || 0;
      const drawing = figure.getBoundingClientRect().height;
      const covered = (r) => r.kind !== "part" || (wide && !(r.total > drawing && r.total > median * 1.2));
      // Each covered view grows to its kind's block, then adds its own navigation, which may wrap.
      const most = { part: 0, tour: 0, valence: 0 };
      for (const r of rows) if (covered(r) && r.kind in most) most[r.kind] = Math.max(most[r.kind], Math.ceil(r.main));
      const heightOf = (r) => r.total + (r.kind in most ? Math.max(0, most[r.kind] - r.main) : 0);
      const floor = Math.ceil(Math.max(...rows.filter(covered).map(heightOf)));
      sizes.clear();
      for (const r of rows) if (r.kind === "part") sizes.set(`${r.valence}:${r.key}`, Math.max(floor, heightOf(r)));
      for (const [kind, px] of Object.entries(most)) panel.style.setProperty(`--reserve-${kind}`, `${px}px`);
      panel.style.setProperty("--reserve-panel", `${floor}px`);
    }

    // Where the page below the explorer would start on screen if the panel's body were `height` tall.
    function pageBelow(height) {
      const next = root.nextElementSibling;
      const gap = next ? next.getBoundingClientRect().top - root.getBoundingClientRect().bottom : 0;
      const pad = panel.getBoundingClientRect().bottom - view.getBoundingClientRect().bottom;
      return Math.max(figure.getBoundingClientRect().bottom, view.getBoundingClientRect().top + height + pad) + gap;
    }

    // A view shorter than the one before never pulls the page below up while it is on screen: the taller height
    // stays until the page below would start under the screen, and only then does the spare height go, out of
    // sight. A click on a part shrinks the panel at once when the page below is off screen, even if it then comes
    // into view (new content in place of the old); a hover only when the page below stays off screen.
    function keepHeight(before, hover) {
      view.style.minHeight = "";
      kept = 0;
      const natural = view.getBoundingClientRect().height;
      if (natural >= before - 1) return;
      view.style.minHeight = `${Math.ceil(before)}px`;
      kept = natural;
      if (!hover && pageBelow(before) >= window.innerHeight) {
        kept = 0;
        view.style.minHeight = "";
        return;
      }
      settleHeight();
    }

    function settleHeight() {
      if (!kept || pageBelow(kept) < window.innerHeight) return;
      kept = 0;
      view.style.minHeight = "";
    }

    // A preview never pushes the page below while it is on screen; a click still opens a taller view.
    function previewFits(key) {
      const now = view.getBoundingClientRect().height;
      return (sizes.get(`${shownValence()}:${key}`) || 0) <= now + 1 || pageBelow(now) >= window.innerHeight;
    }

    function render(hover = false) {
      if (!visible(state.current)) setCurrent("system");
      const key = state.mode === "tour" ? null : state.preview || state.pinned;
      svg.dataset.valence = String(shownValence());
      svg.classList.toggle("is-tour", state.mode === "tour");
      let html;
      if (state.mode === "tour") {
        const step = M.tour[state.step];
        paint(step.parts.includes("system") ? null : step.parts, null);
        html = tourView();
      } else if (key) {
        paint(litFor(key), key);
        html = partView(key);
      } else {
        paint(null, null);
        html = state.mode === "valence" ? valenceView() : introView();
      }
      // Text swaps in place, without a fade: a fading block of text gets its own compositing layer, where
      // the browser rasterizes it differently, so the type visibly changes weight as the fade starts and ends.
      // Unchanged content (a click on the part being previewed) is not replaced at all.
      if (html !== shown) {
        const before = view.getBoundingClientRect().height;
        view.innerHTML = html;
        shown = html;
        keepHeight(before, hover);
      }
      for (const b of controls.querySelectorAll("[data-valence]")) {
        b.setAttribute("aria-pressed", String(Number(b.dataset.valence) === shownValence()));
      }
    }

    function say(text) {
      live.textContent = "";
      requestAnimationFrame(() => { live.textContent = text; });
    }

    function setHash(key) {
      try {
        history.replaceState(null, "", key ? `#explore/${key}` : `${location.pathname}${location.search}`);
      } catch (_) { /* file:// or sandboxed frames */ }
    }

    function setCurrent(key) {
      state.current = key;
      for (const [k, el] of els) el.setAttribute("tabindex", k === key ? "0" : "-1");
    }

    // After an action, bring the panel's first lines into view. Side by side, only when its top has scrolled
    // above the screen, after reading a long part, say. Stacked, the panel sits under the diagram and the page
    // scrolls freely; its first lines go to the top of the screen unless they are already in the upper half.
    function reveal() {
      const top = panel.getBoundingClientRect().top;
      const inView = wideLayout.matches ? top >= 0 : top >= 0 && top <= window.innerHeight / 2;
      if (!inView) window.scrollBy({ top: top - 16, behavior: reduceMotion.matches ? "auto" : "smooth" });
    }

    function pin(key, opts = {}) {
      if (!M.parts[key]) return;
      clearTimeout(hoverTimer);
      if (state.mode === "tour") state.valence = 3;
      if (!visible(key) && state.mode !== "tour") return;
      // A mouse press focuses the part and pins it; the click that follows pins the same part again.
      const again = state.mode === "part" && state.pinned === key;
      state.mode = "part";
      state.pinned = key;
      state.preview = null;
      setCurrent(key);
      render();
      if (!again) {
        say(`${M.parts[key].title}. ${M.parts[key].summary}`);
        setHash(key);
      }
      if (opts.reveal) reveal();
    }

    function unpin() {
      state.pinned = null;
      state.preview = null;
      state.mode = state.valence < 3 ? "valence" : "intro";
      render();
      setHash(null);
    }

    function setValence(n) {
      clearTimeout(hoverTimer);
      state.valence = n;
      state.mode = "valence";
      state.pinned = null;
      state.preview = null;
      render();
      say(`${M.valence[n].title}. ${M.valence[n].tagline}`);
      setHash(null);
    }

    function startTour() {
      clearTimeout(hoverTimer);
      state.mode = "tour";
      state.step = 0;
      state.pinned = null;
      state.preview = null;
      render();
      sayStep();
      setHash("lesson");
    }

    function stepTour(delta) {
      state.step = Math.max(0, Math.min(M.tour.length - 1, state.step + delta));
      render();
      sayStep();
    }

    function endTour() {
      state.mode = "intro";
      state.valence = 3;
      render();
      setHash(null);
    }

    function sayStep() {
      const s = M.tour[state.step];
      say(`Step ${state.step + 1} of ${M.tour.length}. ${s.title}. ${s.text}`);
    }

    // Focus moves with re-rendered panel content, so keyboard users never lose their place.
    function refocus(selector) {
      const el = view.querySelector(selector) || view.querySelector(".panel-title");
      if (el) el.focus({ preventScroll: true });
    }

    function scheduleClear(delay) {
      clearTimeout(clearTimer);
      clearTimer = setTimeout(() => {
        if (state.preview) {
          state.preview = null;
          render(true);
        }
      }, delay);
    }

    svg.addEventListener("pointerover", (e) => {
      if (e.pointerType !== "mouse" || state.mode === "tour") return;
      const hot = e.target.closest(".hot");
      clearTimeout(hoverTimer);
      if (!hot || !visible(hot.dataset.key)) {
        scheduleClear(LINGER);
        return;
      }
      clearTimeout(clearTimer);
      const key = hot.dataset.key;
      if (state.preview === key || (!state.preview && state.mode === "part" && state.pinned === key)) return;
      hoverTimer = setTimeout(() => {
        if (state.mode === "tour" || !visible(key)) return;
        if (!previewFits(key)) return;
        state.preview = key;
        render(true);
      }, HOVER_INTENT);
    });
    svg.addEventListener("pointerleave", (e) => {
      if (e.pointerType !== "mouse") return;
      clearTimeout(hoverTimer);
      scheduleClear(LET_GO);
    });
    svg.addEventListener("click", (e) => {
      const hot = e.target.closest(".hot");
      if (!hot) {
        if (state.mode === "part") unpin();
        else if (state.preview) {
          clearTimeout(clearTimer);
          state.preview = null;
          render();
        }
        return;
      }
      pin(hot.dataset.key, { reveal: true });
    });
    svg.addEventListener("focusin", (e) => {
      const hot = e.target.closest(".hot");
      if (hot && state.mode !== "tour" && state.pinned !== hot.dataset.key) pin(hot.dataset.key);
    });
    svg.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pin(state.current);
        return;
      }
      const moves = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1, Home: "first", End: "last" };
      if (!(e.key in moves)) return;
      e.preventDefault();
      if (state.mode === "tour") endTour();
      const keys = M.order.filter(visible);
      const at = Math.max(0, keys.indexOf(state.current));
      const move = moves[e.key];
      const to = move === "first" ? keys[0] : move === "last" ? keys[keys.length - 1] : keys[(at + move + keys.length) % keys.length];
      setCurrent(to);
      els.get(to).focus();
    });

    root.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      const fromDiagram = svg.contains(document.activeElement);
      if (state.mode === "tour") endTour();
      else if (state.mode === "part" || state.mode === "valence") unpin();
      else return;
      // Focus already on the diagram stays put; refocusing it would select the part again.
      if (!fromDiagram) refocus(".panel-title");
    });

    controls.addEventListener("click", (e) => {
      const v = e.target.closest("[data-valence]");
      if (!v) return;
      setValence(Number(v.dataset.valence));
      // Stacked, the drawing above the switch is what changes, so the page stays where it is.
      if (wideLayout.matches) reveal();
    });

    panel.addEventListener("click", (e) => {
      const go = e.target.closest("[data-go]");
      const tour = e.target.closest("[data-tour]");
      const add = e.target.closest("[data-valence-go]");
      if (go) {
        const nav = go.dataset.nav;
        pin(go.dataset.go);
        refocus(nav ? `[data-nav="${nav}"]` : ".panel-title");
      } else if (e.target.closest("[data-overview]")) {
        unpin();
        refocus(".panel-title");
      } else if (tour) {
        const action = tour.dataset.tour;
        if (action === "next") {
          stepTour(1);
          refocus(state.step === M.tour.length - 1 ? '[data-tour="exit"]' : '[data-tour="next"]');
        } else if (action === "prev") {
          stepTour(-1);
          refocus(state.step === 0 ? '[data-tour="next"]' : '[data-tour="prev"]');
        } else {
          endTour();
          refocus(".panel-title");
        }
      } else if (add) {
        setValence(Number(add.dataset.valenceGo));
        refocus(".panel-title");
      } else if (e.target.closest("[data-tour-start]")) {
        startTour();
        refocus('[data-tour="next"]');
      } else {
        return;
      }
      reveal();
    });

    function followHash() {
      const linked = /^#explore\/([a-z]+)$/.exec(location.hash);
      if (!linked) return false;
      if (linked[1] === "lesson") startTour();
      else if (M.parts[linked[1]]) pin(linked[1]);
      else return false;
      root.scrollIntoView({ block: "start" });
      return true;
    }
    // In-page links such as href="#explore/lesson" arrive as hash changes; the explorer's own
    // updates use replaceState and never fire this event.
    window.addEventListener("hashchange", followHash);
    let resizeFrame = 0;
    window.addEventListener("resize", () => {
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(() => {
        if (Math.round(panel.getBoundingClientRect().width) !== reservedWidth) reserve();
        settleHeight();
      });
    });
    window.addEventListener("scroll", () => {
      if (!kept) return;
      cancelAnimationFrame(keptFrame);
      keptFrame = requestAnimationFrame(settleHeight);
    }, { passive: true });
    reserve();
    if (!followHash()) render();
  }
})();
