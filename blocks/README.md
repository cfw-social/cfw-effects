# Blocks

Reusable CFW Studio building blocks. Each block is a `c-*` folder of instructions (`SKILL.md`) plus supporting scripts, with declared inputs and outputs in `block.yaml`.

Visual and audio treatments (transitions, caption styles, overlays, and the like) do **not** belong here; they live in [`../effects/`](../effects/) as blocks of `kind: effect`. Recipes may still list both in the same `blocks` list. Multiple variations of a block may coexist.

Start a new block from [`_template/`](_template/). See [../docs/DESIGN.md](../docs/DESIGN.md) for the proposed format. This folder is a scaffold; there are no production blocks in this repository yet.
