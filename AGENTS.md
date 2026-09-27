# AGENTS.md

## Status

- Fresh scaffold: `client/` and `server/` are empty placeholders; both stacks are deliberately undecided — do not pick a framework without asking.
- Not a git repository yet.
- No manifests, lockfiles, or CI exist. There are no build/test/lint commands to run until packages are initialized.

## Conventions

- Favor clarity over cleverness; organize code in small, modular units (one concern per module/file) rather than large monolithic files.

## OpenSpec (spec-driven workflow)

- Initialized via `openspec init` (CLI v1.13.x). Specs live in `openspec/specs`, active changes in `openspec/changes`, config in `openspec/config.yaml`.
- Slash commands are defined in `.opencode/commands/` (`/opsx-propose`, `/opsx-explore`, `/opsx-apply`, `/opsx-archive`, `/opsx-sync`, `/opsx-update`) with matching skills in `.opencode/skills/`. They load at session start — restart OpenCode if they don't appear.
- Start feature work with `/opsx-propose "idea"`; don't hand-edit `openspec/specs` directly — go through the opsx workflow so change history stays tracked.

## OpenCode config

- `opencode.jsonc` is agent config (local LLM providers `local-vllm` / `local-sglang` at `136.145.77.x`), not app config — leave it alone when adding project code.
