# DevIntOps

Source of [devintops.org](https://devintops.org): the paper *From Monovalent Dev to Bivalent DevOps to Trivalent DevIntOps: Intelligence as the Third Continuous Loop in Software Engineering*, currently a draft.

Development changes the implementation. Operations changes how it runs. Intelligence changes how it decides.

![Three loops around one system](site/assets/diagrams/02-three-loops.png)

## What's here

| Path | What |
|---|---|
| `site/` | The published site. Plain HTML and CSS plus a few small vanilla scripts; no build step, no webfonts. Every page reads in full without JavaScript. |
| `site/v1/` | The paper, currently a draft. Once it is version 1.0 it is frozen; later versions get new URLs. |
| `site/v1/devintops-v1-draft.pdf` | PDF of the draft. At version 1.0 it becomes `devintops-v1.0.pdf`, for archives such as Zenodo. |
| `site/assets/diagrams/` | Diagrams as SVG (used on the pages and in the PDF) and as 2x PNG (download links and the README). |
| `site/assets/model/three-loops.svg` | The three-loops diagram with every stage, process, loop and the hub addressable, for the model explorer. Generated. |
| `site/assets/model-data.js` | What every word on the diagram means, the walkthrough and the valence notes. Edit explanations here. |
| `site/assets/explorer.js`, `selfcheck.js`, `discuss.js`, `site.js` | The model explorer, the interactive self-check, the GitHub Discussions comments, and small page behaviors such as opening folded sections for deep links. |
| `tools/` | Diagram generator, render script, and `giscus.py`, which fills in the comment widget's GitHub ids. |
| `CITATION.cff`, `.zenodo.json` | Citation metadata for GitHub's "Cite this repository" and for Zenodo. |
| `.github/workflows/pages.yml` | Deploys `site/` to GitHub Pages on every push to `main`. |

## Preview locally

```sh
python3 -m http.server --directory site 8000
# open http://localhost:8000
```

## Regenerate diagrams, social card and PDF

```sh
./tools/render.sh
```

It needs Python 3 and Google Chrome (set `CHROME=/path/to/chrome` elsewhere). The script rebuilds the SVGs (including the explorer's `site/assets/model/three-loops.svg`), renders them to PNG, renders the 1200×630 social card and prints `site/v1/index.html` to the PDF.

## Publish

### One time

1. Register `devintops.org`. A whois lookup on 2026-10-18 showed it unregistered.
2. Create a public repository under your personal GitHub account and push `main`. The site links to `github.com/nodkz/dev-int-ops`; if you use another name, search and replace that string.
3. In the repository, open Settings → Pages and set Source to **GitHub Actions**. The workflow deploys `site/`.
4. In Settings → Pages, set the custom domain to `devintops.org`. Once the certificate is issued, turn on **Enforce HTTPS**.
5. At the registrar, add DNS records:
   - `A` for `devintops.org`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `AAAA` for `devintops.org`: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `CNAME` for `www`: `<your-github-user>.github.io`
6. Verify the domain under your GitHub account settings (Pages → Verified domains), so nobody else can claim it for their Pages site.
7. Turn on comments. In Settings → General → Features, enable **Discussions**. Create a discussion category named `Comments` with the **Announcements** format, so only you and giscus can open threads. Install the giscus app on the repository (<https://github.com/apps/giscus>). Then run `tools/giscus.py` (it uses `gh` and needs read access to the repository) and commit the updated `site/assets/discuss.js`. Until then the pages show a plain link to the repository's discussions. Both pages share one thread, titled `DevIntOps v1.0`.

Prefer a `gh-pages` branch instead of Actions? Run `git subtree push --prefix site origin gh-pages` and choose that branch as the Pages source. `site/CNAME` carries the custom domain.

### For each version

1. Tag a release, for example `v1.0.0`. With the Zenodo GitHub integration switched on, Zenodo archives the release and mints a DOI; `.zenodo.json` supplies the metadata. You can also upload `site/v1/devintops-v1.0.pdf` to Zenodo by hand.
2. Put the DOI in the citation meta tags of `site/v1/index.html` and in `CITATION.cff`, and add a DOI column to the version table in the "Versions and source" section of `site/index.html`.
3. Save `https://devintops.org/v1/` and the PDF in the Wayback Machine: <https://web.archive.org/save>.
4. Share the canonical URL on LinkedIn. If you republish on Medium, set its canonical link to `https://devintops.org/v1/`.

## Versioning

- `/v1/` holds the draft until version 1.0. From then on it stays as published: typos can be fixed; the meaning doesn't change.
- A substantive revision becomes `/v1.1/` or `/v2/`, with an entry in the version history and a new Zenodo version.
- The home page always points to the latest version.

## Before you publish

- Move from DRAFT to version 1.0: replace the DRAFT labels (paper byline, nav, version note, version history, landing ledger, page titles, JSON-LD, `CITATION.cff`, `.zenodo.json`, `tools/pdf_meta.py`, the social card in `tools/build_diagrams.py`), point `tools/render.sh` and the links at `devintops-v1.0.pdf`, and rerun `tools/render.sh`.
- Confirm the publication date (18 October 2026 in the pages, `CITATION.cff` and `sitemap.xml`).
- Confirm the license. CC BY 4.0 is set for text and diagrams, MIT for `tools/`.
- Check that nothing in the text is internal to your employer. It was written to be generic.

## License

Text and diagrams © 2026 Pavel Chertorogov, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Scripts in `tools/` are MIT. See [LICENSE](LICENSE).
