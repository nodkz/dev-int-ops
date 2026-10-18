#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fill the giscus ids in site/assets/discuss.js from GitHub.

Usage: tools/giscus.py [owner/repo] [category]
Defaults come from the CONFIG block in site/assets/discuss.js. Needs the GitHub CLI (gh), logged in to an
account that can read the repository. Before running it: make the repository public, enable Discussions,
create the discussion category (an Announcements-type category, so only maintainers and giscus can open
threads) and install the giscus app (https://github.com/apps/giscus) on the repository.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

JS = Path(__file__).resolve().parent.parent / "site" / "assets" / "discuss.js"
QUERY = """query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    isPrivate
    hasDiscussionsEnabled
    discussionCategories(first: 50) { nodes { id name } }
  }
}"""


def field(source, name):
    match = re.search(rf'{name}: "([^"]*)"', source)
    if not match:
        sys.exit(f"Could not find {name} in {JS}")
    return match.group(1)


def main():
    source = JS.read_text(encoding="utf-8")
    repo = sys.argv[1] if len(sys.argv) > 1 else field(source, "repo")
    category = sys.argv[2] if len(sys.argv) > 2 else field(source, "category")
    owner, _, name = repo.partition("/")
    if not owner or not name:
        sys.exit(f"Expected owner/repo, got {repo!r}")

    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"owner={owner}", "-f", f"name={name}"],
        capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"gh api graphql failed for {repo}:\n{result.stderr.strip()}")
    data = json.loads(result.stdout)["data"]["repository"]
    if data["isPrivate"]:
        sys.exit(f"{repo} is private. giscus only works with public repositories.")
    if not data["hasDiscussionsEnabled"]:
        sys.exit(f"Discussions are off for {repo}. Turn them on in Settings > General > Features.")
    categories = {node["name"]: node["id"] for node in data["discussionCategories"]["nodes"]}
    if category not in categories:
        sys.exit(f'{repo} has no discussion category named "{category}". Existing: {", ".join(categories) or "none"}.')

    for key, value in (("repo", repo), ("repoId", data["id"]), ("category", category),
                       ("categoryId", categories[category])):
        source = re.sub(rf'{key}: "[^"]*"', f'{key}: "{value}"', source, count=1)
    JS.write_text(source, encoding="utf-8")
    print(f"giscus configured for {repo}, category {category!r} ({categories[category]})")
    print("Remember: the giscus app must be installed on the repository: https://github.com/apps/giscus")


if __name__ == "__main__":
    main()
