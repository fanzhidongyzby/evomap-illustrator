# EvoMap Illustrator

A generic SVG/PNG renderer for algorithms, workflows, architectures and node relationships. It ships an original EvoMap-inspired default theme, customizable themes and a verified Lomuto quicksort example. It does not ship a private VI manual, logos, photography or font files.

## Install as a Claude Code skill

```bash
git clone https://github.com/fanzhidongyzby/evomap-illustrator.git ~/.claude/skills/evomap-illustrator
```

Do not overwrite an existing installation. Use its Git repository or back it up first. The Python renderer requires Python 3.9+ and only the standard library.

PNG export needs `rsvg-convert` (librsvg): `brew install librsvg` on macOS, or `sudo apt-get install librsvg2-bin fonts-noto-cjk` on Debian/Ubuntu. Software is not installed automatically. `--svg-only` works without the PNG backend, but does not count as delivering PNG.

## Render any diagram

```bash
python3 -I scripts/render.py spec --input examples/architecture.json --output-dir illustrations --name architecture --scale 2
python3 -I scripts/render.py spec --input examples/architecture.json --theme examples/slate-theme.json --output-dir illustrations --name architecture-slate --scale 2
```

The spec API has text, rect, circle, path, arrow, line, array and section elements. Layout is explicit: text is escaped, not executable HTML/SVG; long text is not automatically wrapped. See [spec format](references/spec-format.md).

`--theme` merges safe JSON overrides for colors, fonts and geometry. Missing tokens inherit the default. A spec can also contain an inline `theme` object. Each Figure keeps its own theme; customization does not mutate another diagram or the default theme.

## Quicksort example

```bash
python3 -I scripts/render.py quicksort --values 6,3,8,1,7,2,5 --output-dir illustrations --name quicksort --scale 2
```

The single-page template accepts 2–7 integers (at most three printed characters each). It computes actual Lomuto comparisons/swaps and verifies partition invariants, recursive ranges and the sorted result. More complex cases should use paged specs; the trace algorithm is not restricted to the template size.

Visible promotional titles and footers are off by default; `--teaching-page` restores the optional teaching-page header/footer. The default diagram still includes semantic module labels and the algorithm's necessary explanations. Use a custom spec for a tighter article illustration.

## Output and compatibility

SVG and PNG share one geometry. `--scale` changes physical PNG pixels; a 1200×511 spec with scale1 produces exactly 1200×511, while scale2 doubles both dimensions. Preserve aspect ratio instead of stretching content.

Output names support Unicode letters/numbers, underscores and hyphens, not paths. Existing files are never overwritten. PNG export is capped at 50 million pixels. The Python API still exports `Figure`, `from_spec`, `quicksort_trace`, `quicksort_figure` and `export`; existing calls without a theme keep the original theme.

Default fonts use system fallback lists. A font-family name is not a bundled font license. Review the actual PNG for missing glyphs, collisions, line direction and crop. Programmatic checks do not prove a diagram's domain claims or accessibility under every theme.

## Local preferences

Optional `.local/profile.json` is ignored by Git. It can specify `theme_file` for a private local theme and guidance such as language/content-only preference. Relative local theme paths are resolved against this skill directory. The public repository does not distribute local preferences or source reference materials.

The EvoMap-inspired profile prefers opaque white, black/gray structure, limited accent color and high-contrast labels. Other themes may use different colors; these are not arbitrary-photo or scientific-plot rules. Never encode meaning with color alone. See [style principles](references/style-guide.md).

## Tests and Git sync

```bash
python3 -I scripts/test_render.py
python3 -I scripts/check_release.py
python3 -I scripts/repo_sync.py status
python3 -I scripts/repo_sync.py pull
```

Edit on a working branch; test and commit before an explicitly requested push. `repo_sync.py push` performs a normal push only, never auto-commits or force-pushes. A fetched upstream commit is compared to local HEAD, while ignored local preferences intentionally remain local.

Enable the optional push gate with `git config core.hooksPath .githooks`. It runs tests and checks the public package for private paths, document locators or credentials; it does not use model APIs.

## License

Original code, theme implementation, documentation and synthetic examples are MIT licensed. Brand names, third-party media and fonts retain their own rights; this repository does not grant access to or redistribution rights for an original VI manual or other private assets.
