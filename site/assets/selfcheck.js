// Interactive self-check: turns each ol[data-selfcheck] into six yes/no questions with a live verdict.
// The verdict rules come from the paper at /v1/. Answers stay in the page; nothing is stored or sent.
// data-paper on the list is the path to the paper ("v1/" on the home page, "" on the paper itself).
(() => {
  "use strict";
  const VERDICTS = {
    bivalent: {
      title: "Bivalent",
      text: "Your answers don't show learning across tasks yet, however many agents you run. Start small: one failure class, one stage, one owner. Escapes past code review make a good first slice.",
      link: ["start", "How to start small"],
    },
    unproven: {
      title: "Trivalent in shape, not yet in proof",
      text: "The loop may exist, but nobody can show that it works, or it grades its own work. Let a named owner, not the loop, decide how lessons are judged. Have each lesson say what it should change and by when, and check that against a baseline, beginning with the repeat rate per failure class.",
      link: ["metrics", "How to measure the loop"],
    },
    fragile: {
      title: "Trivalent, with fragile memory",
      text: "Lessons live in people and documents, or wrong and stale ones can't be taken back. Keep them in a versioned store with their evidence, linked to the rules and settings they change. Give each one an expiry date, so stale lessons leave unless someone renews them, and make sure a wrong one can be retracted everywhere.",
      link: ["governance", "Owner, memory and limits"],
    },
    trivalent: {
      title: "Trivalent",
      text: "Your answers describe a third loop with an owner, memory and a metric. Answers are not proof: test whether it pays after the cost of learning.",
      link: ["falsification", "How to test whether it pays"],
    },
  };
  const PENDING = "Questions 1 and 2 look for learning across tasks; 3 and 4 for checks the loop doesn't grade itself; 5 and 6 for memory that lasts and stays clean. Leave a question open while its outcome is pending.";

  document.querySelectorAll("ol[data-selfcheck]").forEach((list, n) => {
    const items = Array.from(list.children);
    const prefix = list.id || `selfcheck-${n + 1}`;
    const paper = list.dataset.paper || "";
    items.forEach((li, i) => {
      const row = document.createElement("div");
      row.className = "check-row";
      const question = document.createElement("span");
      question.id = `${prefix}-q${i + 1}`;
      question.append(...li.childNodes);
      const answers = document.createElement("span");
      answers.className = "answers no-print";
      answers.setAttribute("role", "radiogroup");
      answers.setAttribute("aria-labelledby", question.id);
      answers.innerHTML = ["Yes", "No"].map((label) =>
        `<label><input type="radio" name="${prefix}-a${i + 1}" value="${label.toLowerCase()}"><span>${label}</span></label>`).join("");
      row.append(question, answers);
      li.append(row);
    });

    const out = document.createElement("div");
    out.className = "verdict no-print";
    out.setAttribute("aria-live", "polite");
    out.innerHTML = '<p class="verdict-title"></p><p class="verdict-text"></p><p class="verdict-link"></p>' +
      '<p class="verdict-foot"><span class="verdict-count"></span> Your answers stay in this page; nothing is stored or sent. ' +
      '<button type="button" class="link-button" data-reset>Clear answers</button></p>';
    list.after(out);

    const answerOf = (i) => {
      const checked = items[i].querySelector("input:checked");
      return checked ? checked.value : null;
    };

    function verdict(a) {
      const no = (i) => a[i] === "no";
      const yes = (i) => a[i] === "yes";
      if (no(0) || no(1)) return "bivalent";
      if (!yes(0) || !yes(1)) return "pending";
      if (no(2) || no(3)) return "unproven";
      if (!yes(2) || !yes(3)) return "pending";
      if (no(4) || no(5)) return "fragile";
      return yes(4) && yes(5) ? "trivalent" : "pending";
    }

    function update() {
      const a = items.map((_, i) => answerOf(i));
      const answered = a.filter(Boolean).length;
      const level = verdict(a);
      const v = VERDICTS[level];
      out.dataset.level = level;
      out.querySelector(".verdict-title").textContent = level === "pending"
        ? "No verdict yet"
        : answered < items.length ? `So far: ${v.title}` : v.title;
      out.querySelector(".verdict-text").textContent = level === "pending" ? PENDING : v.text;
      out.querySelector(".verdict-link").innerHTML = level === "pending"
        ? ""
        : `<a href="${paper}#${v.link[0]}">${v.link[1]}</a>`;
      out.querySelector(".verdict-count").textContent = `${answered} of ${items.length} answered.`;
    }

    list.addEventListener("change", update);
    out.querySelector("[data-reset]").addEventListener("click", () => {
      for (const input of list.querySelectorAll("input:checked")) input.checked = false;
      update();
      const first = list.querySelector("input");
      if (first) first.focus();
    });
    update();
  });
})();
