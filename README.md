# CFW Studio

Public source of truth for CFW Social **building blocks** and **recipes**.

- **Blocks** (`c-*`) are reusable Lego pieces: instructions plus supporting scripts, each with declared inputs and outputs. Effects are one kind of block. Multiple variations of a block may coexist.
- **Recipes** are guiding documents that compose those blocks. A recipe's inputs are the union of its blocks' required inputs, and the recipe declares its final output. Any agent can read a recipe and run it as-is, or compose a new one.

People and bots contribute through pull requests. An admin reviews sample outputs and merges. After merge, CFW is intended to snapshot the changed files into immutable, fingerprinted copies so every render server uses the same bytes. Posts that reach Reviews are intended to be tagged with the recipe and block fingerprints, which supports usage tracking and retirement.

## Status

**Proposed, not built.** This repository currently holds the target design, contribution guides, and empty scaffolds. The merge-to-snapshot sync, Marketplace listing from those snapshots, and Reviews tagging are not implemented yet. A folder here is not, by itself, a recipe already runnable in CFW.

Start here:

- [docs/DESIGN.md](docs/DESIGN.md) — full target design
- [docs/DECISIONS.md](docs/DECISIONS.md) — why this shape was chosen
- [docs/MIGRATION.md](docs/MIGRATION.md) — how to get here from today's publish path
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to add a block or recipe
- [AGENTS.md](AGENTS.md) — instructions for coding agents

## Layout

```text
blocks/            reusable blocks (c-*), including _template/
recipes/           recipes (p-*) composed of blocks, including _template/
docs/              design, decisions, and migration
```

## License

This repository is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE). Confirm that this is the intended license before contributing substantial new blocks or recipes.
