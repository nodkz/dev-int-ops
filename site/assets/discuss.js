// Reader comments through GitHub Discussions, rendered by giscus (https://giscus.app).
// tools/giscus.py fills repoId and categoryId once the repository exists. Until then the page shows a plain link.
(() => {
  const CONFIG = {
    repo: "nodkz/dev-int-ops",
    repoId: "",
    category: "Comments",
    categoryId: "",
  };

  const box = document.querySelector("[data-discuss]");
  if (!box) return;
  if (!CONFIG.repoId || !CONFIG.categoryId) {
    box.dataset.state = "unconfigured";
    return;
  }

  const load = () => {
    const script = document.createElement("script");
    const attrs = {
      repo: CONFIG.repo,
      "repo-id": CONFIG.repoId,
      category: CONFIG.category,
      "category-id": CONFIG.categoryId,
      mapping: "specific",
      term: box.dataset.term || "DevIntOps",
      strict: "1",
      "reactions-enabled": "1",
      "emit-metadata": "0",
      "input-position": "top",
      theme: "light",
      lang: "en",
      loading: "lazy",
    };
    for (const [key, value] of Object.entries(attrs)) script.setAttribute(`data-${key}`, value);
    script.src = "https://giscus.app/client.js";
    script.crossOrigin = "anonymous";
    script.async = true;
    box.dataset.state = "loading";
    box.append(script);
  };

  // Contact giscus.app only when the reader gets near the discussion.
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        io.disconnect();
        load();
      }
    }, { rootMargin: "600px 0px" });
    io.observe(box);
  } else {
    load();
  }
})();
