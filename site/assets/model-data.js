// Content for the model explorer (assets/explorer.js): what every word on the three-loops diagram means.
// Plain data, kept in step with the paper at /v1/. Edit text here; the explorer only renders it.
window.DEVINTOPS_MODEL = {
  loops: {
    dev: { name: "Development", verb: "changes the implementation", stages: ["plan", "code", "build", "test"] },
    ops: { name: "Operations", verb: "changes how it runs", stages: ["release", "deploy", "operate", "monitor"] },
    int: { name: "Intelligence", verb: "changes how it decides", stages: ["understand", "predict", "orchestrate", "learn"] },
  },

  // Reading order for the keyboard: each ring in the order the diagram draws it,
  // with every continuous process between the two stages it spans.
  order: ["system",
    "dev", "plan", "integration", "code", "build", "delivery", "test",
    "ops", "release", "deployment", "deploy", "operate", "feedback", "monitor",
    "int", "understand", "reasoning", "predict", "orchestrate", "adaptation", "learn"],

  parts: {
    system: {
      kind: "hub", title: "System",
      summary: "The one system all three loops act on.",
      body: "In the engineering application it is how we build and run software: the repositories, pipelines, agents, people and rules. Put the product in the middle instead and the same pattern applies, with its own owners and memory: the product changes how it decides without waiting for a release.",
      facts: [["Development", "changes its implementation"], ["Operations", "changes how it runs"], ["Intelligence", "changes how it decides"]],
      noteLabel: "Valence", note: "A metaphor: count the continuous loops bonded to the system, one for Dev, two for DevOps, three for DevIntOps. Switch valence above the diagram to see each step.",
    },

    dev: {
      kind: "loop", loop: "dev", title: "Development",
      summary: "Builds and verifies changes. Its core is flow and quality.",
      body: "Small changes flow from plan to tested code without waiting in queues, with people and agents in one shared repository. Quality is built in on the way, not inspected at the end.",
      facts: [["Stages", "Plan → Code → Build → Test"], ["Continuous", "Integration, Delivery"], ["Unit of work", "a change"],
        ["Clock", "per change, in hours or days"], ["Metric", "lead time, task completion"], ["Without it", "nothing ships"]],
    },
    ops: {
      kind: "loop", loop: "ops", title: "Operations",
      summary: "Ships and runs the system. Its core is stability and observability.",
      body: "Releases reach production through shared, standard pipelines and runbooks. The system stays available, scaled and within budget, and what it does in production stays visible to everyone who builds it.",
      facts: [["Stages", "Release → Deploy → Operate → Monitor"], ["Continuous", "Deployment, Feedback"], ["Unit of work", "a release, an incident"],
        ["Clock", "per deploy and per alert, in seconds or minutes"], ["Metric", "change failure rate, incident rate, time to restore"],
        ["Without it", "nothing survives production"]],
    },
    int: {
      kind: "loop", loop: "int", title: "Intelligence", isNew: true,
      summary: "Turns outcomes into lessons that change how each stage decides, and checks whether they helped. Its core is memory and judgment.",
      body: "Outcomes from every stage flow in: escaped bugs, incidents, review feedback, rollbacks, cost spikes, checks that never fire, changes that went well. Memory is versioned experience with its sources, kept across tasks and people; judgment weighs the options, including doing nothing, and selects one within the owners' limits. Lessons flow back into each stage's own rules, evals, context and thresholds, with the stage owner's approval, and a named team owns the loop, its memory and its metric.",
      noteLabel: "Beyond failures", note: "A lesson can also make a pattern that worked the default, propose retiring a check that never fires, let a safe gate move faster or send simple work to a cheaper agent. Lessons loosen defaults as well as tighten them.",
      facts: [["Stages", "Understand → Predict → Orchestrate → Learn"], ["Continuous", "Reasoning, Adaptation"], ["Unit of work", "an outcome in, a lesson out"],
        ["Clock", "per outcome, keeping what it learned in between"], ["Metric", "time to lesson, payoff per lesson (for a failure class, measured by its repeat rate)"],
        ["Without it", "nothing compounds: every task starts from the same defaults"]],
    },

    plan: {
      kind: "stage", loop: "dev", title: "Plan",
      summary: "Turn goals and evidence into a roadmap and specs.",
      body: "Decide what to build next and why. A useful plan is a bet someone can check later: a goal, a spec, acceptance criteria and a rough size.",
      facts: [["In", "goals, user feedback, findings from production"], ["Out", "specs with acceptance criteria"], ["Watch", "rework caused by unclear specs"]],
      noteLabel: "With the third loop", note: "Plan starts from what earlier outcomes taught. If one kind of spec keeps causing rework, the lesson arrives as a constraint in the spec template, not as a slide in a retro. A spec that led to a clean, fast delivery can become the template the same way.",
    },
    code: {
      kind: "stage", loop: "dev", title: "Code",
      summary: "Implement the change, with agents and people in one repo.",
      body: "Write the change, review it and merge it. Agents draft code and review comments; people own the merge.",
      facts: [["In", "a spec"], ["Out", "a reviewed, merged change"], ["Watch", "review findings, changes reverted after merge"]],
      noteLabel: "With the third loop", note: "The coding agent's context and the review rules carry earlier lessons. A change that repeats a known escape gets flagged in review, because that class escaped once before.",
    },
    build: {
      kind: "stage", loop: "dev", title: "Build",
      summary: "Turn code into deployable artifacts, automatically.",
      body: "Compile, package and scan every change the same way, so what you test is exactly what you ship.",
      facts: [["In", "a merged change"], ["Out", "a versioned artifact"], ["Watch", "build time, broken builds, flaky steps"]],
      noteLabel: "With the third loop", note: "Build failures form classes too. A dependency break that keeps coming back turns into a pinned version or a pre-merge check, proposed to the build owner. Cache and parallel settings that cut build time become defaults the same way.",
    },
    test: {
      kind: "stage", loop: "dev", title: "Test",
      summary: "Check the change works before anyone depends on it.",
      body: "Run unit, integration and end-to-end tests, plus evals for anything an AI agent does.",
      facts: [["In", "an artifact"], ["Out", "a verdict with evidence"], ["Watch", "escaped defects, flaky tests"]],
      noteLabel: "With the third loop", note: "Most escapes point at a missing or weak check. The third loop proposes the test or eval that would have caught it, replays it on the escaped change, and keeps it only if it fires and holds up on other changes. Tests that have never failed and cost minutes on every run get flagged for review: a clean record alone doesn't prove a test is useless.",
    },

    release: {
      kind: "stage", loop: "ops", title: "Release",
      summary: "Package a tested build into a versioned release, ready to ship.",
      body: "Decide what goes out together, write the release notes, and attach the evidence: test results, approvals and known risks.",
      facts: [["In", "a verified build"], ["Out", "a release candidate"], ["Watch", "release frequency, rollback readiness"]],
      noteLabel: "With the third loop", note: "Release risk can be estimated from history: changes like this one, in this area, failed this often. The gate threshold is decision state the third loop can tune within an agreed band.",
    },
    deploy: {
      kind: "stage", loop: "ops", title: "Deploy",
      summary: "Roll out step by step through rings and feature flags.",
      body: "Move the release to production gradually, ring by ring and flag by flag, and halt automatically on bad signals.",
      facts: [["In", "a release"], ["Out", "the change running in production"], ["Watch", "change failure rate, deployment frequency"]],
      noteLabel: "With the third loop", note: "Rollout speed becomes a learned default. After two incidents caused by config changes, config rollouts move slower and wait longer at the first ring, while changes in areas with a clean record move faster.",
    },
    operate: {
      kind: "stage", loop: "ops", title: "Operate",
      summary: "Keep the system available, scaled and within budget.",
      body: "Run the service: capacity, cost, on-call and incident response. When something breaks, restore service first.",
      facts: [["In", "alerts, incidents, load"], ["Out", "a running, restored system"], ["Watch", "availability, time to restore, cost"]],
      noteLabel: "With the third loop", note: "Operations changes this run, for example with a rollback. The third loop changes next time's default: the alert threshold, the missing runbook step, the rollout guard. An alert nobody acts on is proposed for retirement.",
    },
    monitor: {
      kind: "stage", loop: "ops", title: "Monitor",
      summary: "Watch real behavior: telemetry, errors and user signals.",
      body: "Collect what production actually does: metrics, logs, traces, errors, cost and what users say.",
      facts: [["In", "production behavior"], ["Out", "signals and outcomes"], ["Watch", "time to detect, alert noise"]],
      noteLabel: "With the third loop", note: "Monitor feeds two loops. Its signals go back to Plan, as in DevOps, and every outcome also enters Understand, where it can become a lesson.",
    },

    understand: {
      kind: "stage", loop: "int", title: "Understand",
      summary: "Read goals, context and outcomes: what is asked, known and unclear.",
      body: "A goal or an outcome arrives: a change about to ship, an escaped bug, an incident, a flaky verdict, a review comment accepted or dismissed, a rollback, a cost spike, user feedback, a change that went better than expected. Work out what is asked or what happened, why, and which class it belongs to: a failure class, a kind of waste, or a result worth repeating.",
      facts: [["In", "a goal, or an outcome from any stage"], ["Out", "a stated goal or a classified outcome"], ["Watch", "time from outcome to class"]],
      noteLabel: "Example", note: "A retry path lacks a null check and the bug escapes review. The class: unchecked optional in retry code.",
    },
    predict: {
      kind: "stage", loop: "int", title: "Predict",
      summary: "Weigh options, including no action, and select one within the limits.",
      body: "Compare the permitted options against the goal, risk, cost and past experience: for an escaped bug, the stages that could most cheaply have caught it. Select one; changing nothing is a valid answer. State the expected effect, its uncertainty and the cost.",
      facts: [["In", "a goal or a classified outcome, the permitted options and relevant memory"], ["Out", "a selected change, or a decision to change nothing"], ["Watch", "lessons proposed against lessons kept"]],
      noteLabel: "Example", note: "A review rule plus an eval, expected to catch the class at review, at the cost of a few false positives.",
    },
    orchestrate: {
      kind: "stage", loop: "int", title: "Orchestrate",
      summary: "Send each decision to the stage or agent allowed to act on it.",
      body: "Route the change through that stage's own mechanism and its owner's approval: more context for the coding agent, a review rule, an eval or test, a gate threshold, a slower rollout, a constraint in the spec.",
      facts: [["In", "a selected decision"], ["Out", "a change to one stage's rules, evals or context, or a recorded no-op"], ["Watch", "time to lesson"]],
      noteLabel: "Example", note: "The rule ships to review as a draft. Once its replay passes, the review owner approves it. Next time's default has changed.",
    },
    learn: {
      kind: "stage", loop: "int", title: "Learn",
      summary: "Compare expected with actual and keep, revise or retract the lesson.",
      body: "Replay first: does the changed stage now handle the original case as intended? Then try it on cases it wasn't written from, run it where it can't block yet, and watch the class for a fixed window against a baseline. One replay never proves a broad improvement. Keep, narrow, decay or retract the lesson, and record why.",
      facts: [["In", "the lesson and what happened next"], ["Out", "a kept, narrowed or retracted lesson"], ["Watch", "payoff against a baseline, and how often expected effects come true"]],
      noteLabel: "Example", note: "Replayed on the escaped change, the rule fires. After 60 days it has fired twice, once wrongly, so it gets narrowed.",
    },

    integration: {
      kind: "process", loop: "dev", title: "Continuous Integration", spans: ["plan", "code"],
      summary: "Merge small changes often, and check each one against the main line.",
      body: "Plan and Code meet in small, frequent merges, so everyone builds on current code and conflicts stay small. Every merge triggers an automatic build and test. Like every process label on the diagram, it marks the main area of responsibility, not a hard boundary.",
      noteLabel: "With the third loop", note: "The checks on every merge carry lessons from earlier outcomes: new ones for known escapes, and fewer that only cost time.",
    },
    delivery: {
      kind: "process", loop: "dev", title: "Continuous Delivery", spans: ["build", "test"],
      summary: "Keep every change in a releasable state.",
      body: "Every change is built, tested and packaged the same way, so shipping becomes a business decision instead of an engineering project.",
      noteLabel: "With the third loop", note: "Lessons arrive here as new tests, evals and build checks, each one replayed on the case that prompted it.",
    },
    deployment: {
      kind: "process", loop: "ops", title: "Continuous Deployment", spans: ["release", "deploy"],
      summary: "Ship every change that passes the checks, automatically and gradually.",
      body: "Verified changes go to production on their own, behind rings, feature flags and automatic rollback.",
      noteLabel: "With the third loop", note: "Gate thresholds and rollout speed become learned defaults instead of fixed settings.",
    },
    feedback: {
      kind: "process", loop: "ops", title: "Continuous Feedback", spans: ["operate", "monitor"],
      summary: "Return what production shows to the people and agents who build.",
      body: "Errors, performance, cost and user behavior flow back from running the system to planning it. This is the arrow that closes the DevOps figure-eight.",
      noteLabel: "With the third loop", note: "The same signals also enter Understand, where outcomes become lessons for every stage, not only for the next spec.",
    },
    reasoning: {
      kind: "process", loop: "int", title: "Continuous Reasoning", spans: ["understand", "predict"],
      summary: "Explain goals and outcomes and weigh options as they happen.",
      body: "Reasoning can start from a goal before anything fails, or from an outcome after. Instead of waiting for a retrospective, it explains and classifies what happened and weighs candidate changes, each with an expected effect, a risk and a cost.",
      noteLabel: "Why now", note: "Models can read incident narratives, review threads and test logs and draft a structured lesson in minutes. Drafting is cheap; validating is not, which is why the next process exists.",
    },
    adaptation: {
      kind: "process", loop: "int", title: "Continuous Adaptation", spans: ["orchestrate", "learn"],
      summary: "Apply lessons through each stage's own mechanisms, then check that they worked.",
      body: "Lessons change rules, evals, context and thresholds with the owner's approval. Each one is replayed, tested beyond its first case, watched for a fixed window, then kept, narrowed, decayed or retracted.",
      noteLabel: "Limits", note: "People own goals, permissions and boundaries. Context and thresholds within a band can change automatically, blocking rules and policy need a person, and merges never happen on their own. Nothing the loop learns can widen a permission or change how the loop is scored.",
    },
  },

  valence: {
    1: { title: "Monovalent: Dev", tagline: "We build it.",
      text: "One loop bonded to the system. Development changes the implementation, and someone else runs it. What production shows reaches the builders late, if at all." },
    2: { title: "Bivalent: DevOps", tagline: "We build it and run it.",
      text: "Two loops bonded to one system. Monitor feeds back into Plan, and one team owns both loops. Putting an AI agent into every box of this figure-eight makes it faster. Unless something carries lessons across tasks and checks them, it is still bivalent." },
    3: { title: "Trivalent: DevIntOps", tagline: "We build it, run it, and it learns how to decide.",
      text: "Three loops bonded to one system. Outcomes from every stage flow into Understand, and lessons flow back into every stage through that stage's own mechanisms, with its owner's approval." },
  },

  // "Follow one lesson": the paper's escaped null check, step by step. valence 2 hides the third loop.
  tour: [
    { parts: ["code", "release", "deploy"], valence: 2, title: "A gap ships",
      text: "An illustrative case: a change adds a retry path. Review passes, tests pass, and the release rolls out through the rings. Nobody notices that one optional value is never checked." },
    { parts: ["monitor"], valence: 2, title: "Production notices",
      text: "The retry path finally runs and errors spike. Monitor raises an alert." },
    { parts: ["operate", "code"], valence: 2, title: "DevOps closes the incident",
      text: "On call rolls back and restores service, and Development fixes the bug. In a bivalent system the story often ends here, with a postmortem and a follow-up ticket." },
    { parts: ["understand"], valence: 3, title: "The outcome enters the third loop",
      text: "Understand reads the diff, the review thread and the incident timeline, and files the escape under a failure class: unchecked optional in retry code." },
    { parts: ["predict"], valence: 3, title: "Which stage could have caught it?",
      text: "Predict weighs where a bounded change could have caught it most cheaply, changing nothing included, and selects review: a review rule plus an eval, with the expected effect, the risk and the cost." },
    { parts: ["orchestrate", "code"], valence: 3, title: "Change the stage, with its owner",
      text: "Orchestrate ships the rule to review as a draft, through the review step's own mechanism. Once its replay passes, the review owner approves it. Next time's default has changed." },
    { parts: ["learn"], valence: 3, title: "Did it work?",
      text: "Replayed on the escaped change, the rule fires, and a run over recent changes counts its false positives. After 60 days it has fired twice, once wrongly, so it gets narrowed. Firings are not avoided escapes: the score is the class's repeat rate against a baseline." },
    { parts: ["system"], valence: 3, title: "One incident, three loops",
      text: "Operations restored service. Development fixed the bug. Intelligence changed what catches it next time." },
  ],
};
