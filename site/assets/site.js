// Small page behaviors. Opens a folded section (the vocabulary, the paper's contents) when a link points
// into it, so deep links such as #term-lesson always land on visible text.
(() => {
  "use strict";
  function openTarget() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (!id || id.includes("/")) return;
    const target = document.getElementById(id);
    const folded = target && target.closest("details:not([open])");
    if (!folded) return;
    folded.open = true;
    target.scrollIntoView({ block: "start" });
  }
  window.addEventListener("hashchange", openTarget);
  openTarget();
})();
