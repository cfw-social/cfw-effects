# Effects

Visual and audio treatments an agent can snap into a recipe: transitions, confetti, fireworks, caption styles, overlays, sound effects, and music beds.

An **effect is a block of `kind: effect`**. It has the same shape as any other building block — declared inputs and outputs, instructions, and supporting scripts — but it lives in this folder so the library of looks and sounds is easy to browse. A recipe references an effect the same way it references any other block: by id and variation, in its `blocks` list.

Effects are Lego bricks, not whole instruction sheets. A caption style does not produce a finished reel on its own; a recipe such as a clipper or a talking-head reel calls that style as one step.

## Layout

Each effect is a folder (proposed id prefix `e-*`):

- `effect.yaml` — the manifest: identity, `kind: effect`, variation, and declared inputs and outputs
- `SKILL.md` — instructions an agent follows to apply the effect
- `scripts/` — supporting scripts the instructions call
- a **preview** (see the template) so reviewers can judge the look or sound without running the effect themselves

Start a new effect from [`_template/`](_template/). See [../docs/DESIGN.md](../docs/DESIGN.md) for the proposed format. This folder is a scaffold; there are no production effects in this repository yet.

Multiple variations of an effect may coexist (for example two caption styles). Add a new variation rather than silently rewriting one that recipes already use.
