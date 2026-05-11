# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-11

### Changed (breaking — install path)

- **Skill is now self-contained at `skills/ref-downloader/`.** Python sources
  moved from repo root to `skills/ref-downloader/scripts/`; `config.example.toml`
  moved to `skills/ref-downloader/`. The skill folder can now be copied
  directly to any agent framework's skill directory (`~/.claude/skills/`,
  `~/.codex/skills/`, `.github/skills/`, `.agents/skills/`) without dragging
  the rest of the repo along — Level-2 portable skill structure per
  `anthropics/skills` convention.
- `_config.py` constant `PACKAGE_DIR` → `_SKILL_DIR`; it now points to the
  skill root (parent of `scripts/`) so config files sit one level up from
  scripts — matches user-expected layout (config visible at skill root, not
  buried inside scripts/).
- `run_ref_downloader.py` constant `SKILL_DIR` → `SCRIPTS_DIR` to reflect the
  actual semantics after the move.
- Removed `skills/ref-downloader/agents/openai.yaml`. Codex's own skill format
  is now SKILL.md frontmatter (matching Anthropic's spec); the bespoke
  `openai.yaml` UI metadata file was not portable across frameworks.
  Users who specifically need Codex UI metadata can add their own.
- README install section restructured: "as agent skill" (per-framework
  `cp -r` command) vs "as Python tool" (clone + pip + pytest).
- `tests/conftest.py` `sys.path` now points to
  `skills/ref-downloader/scripts/` instead of repo root.

### Migration note for existing users

If you previously installed by cloning the repo and running scripts from root:
- Your local `config.local.toml` at repo root → move to `skills/ref-downloader/config.local.toml`
- Direct script invocations `python run_ref_downloader.py X` → become `python skills/ref-downloader/scripts/run_ref_downloader.py X`
- Agent-mode users: re-copy `skills/ref-downloader/` to your framework's skill path; old `SKILL.md` at repo root is gone.

## [0.1.0] — 2026-05-10

Initial open-source release. Refactored from a personal Claude Code skill;
all institution-specific and personal-path constants have been extracted to
configuration.

### Added

- Three-script pipeline: `extract_refs.py`, `validate_refs.py`,
  `download_refs.py` driven by single-entry wrapper `run_ref_downloader.py`
- Config layer (`_config.py`) reading TOML + environment variables
- `config.example.toml` documenting all options; `config.local.toml`
  gitignored for user-specific values
- Bilingual documentation: English `README.md` + `README.zh.md`
- Issue templates: `bug-report.md`, `new-publisher.md`
- `SECURITY.md` describing Edge profile access and recommendation for a
  dedicated profile
- `docs/SUPPORTED_PUBLISHERS.md` extracted from the original SKILL.md as
  reference documentation for contributors
- `[institution]` config section enabling per-organization SSO detection
  (auth host / URL / page title patterns) and DOI-level access exclusions
- Non-interactive mode: `--yes` flag and tty-detection in `extract_refs.py`
- Per-field environment variable overrides (`REF_DOWNLOADER_MAILTO`,
  `_ZOTERO_DB`, `_EDGE_PROFILE`, `_DISABLE_EXTENSIONS`, `_CONFIG`)
- Bilingual highlights table at the top of `README.md` and `README.zh.md`,
  framed as user-value-first ("what you get — *how it's distinctively
  delivered*"). 5 rows, mirrored row-for-row between languages, scannable
  in seconds.
- **Installable skill package**: agent-mode runbook now lives under
  `skills/ref-downloader/`, keeping the repository root as the human-facing
  Python project while the skill bundle stays small and installable.
- `skills/ref-downloader/agents/openai.yaml`: UI metadata for the packaged skill.
- **SKILL.md slim entry**: agent-mode runbook reduced from 420 → 105 lines,
  with the long 8-step manual flow + DOI-resolution code + `PUBLISHER_MAP`
  extension procedure moved to
  [skills/ref-downloader/references/agent-runbook.md](skills/ref-downloader/references/agent-runbook.md).
  SKILL.md now follows skill-creator best practice: trigger phrases,
  primary entry command, pre-flight checklist, common-failure lookup table,
  pointer to the extended runbook.
- README and README.zh.md gain a `status-beta` badge + an explicit "Status:
  beta (v0.1.0)" status line so users calibrate expectations.
- **Offline pytest suite** (`requirements-dev.txt` + `tests/test_*.py`):
  10 unit tests covering the config loader (chain merge order, env-var
  overrides, malformed-TOML exit, schema validation) + publisher detection
  (DOI prefix + journal fallback) + project-name sanitization.
  Runs in <1s, no Playwright dependency.
- `docs/architecture.md` (new): condensed design rationale for contributors
  (why real Edge profile, why one big `download_refs.py`, why the
  `auth_loading_titles` ambiguity is intentional, what's deliberately out
  of scope).
- `docs/plans/` (removed): the internal design + implementation diaries are
  no longer carried in the public-facing repo. Their substantive content
  lives in `docs/architecture.md`; their procedural content is captured
  in git history + commit messages.

### Publishers

Initial coverage (varying maturity; see `docs/SUPPORTED_PUBLISHERS.md`):
ACS, Nature, Science, Elsevier, Wiley, RSC, Springer, PNAS, ECS, IOP, AIP,
AVS, IEEE, OSA, KPS, Beilstein, APS, Annual Reviews, Taylor & Francis.

### Known limitations

- Windows + Microsoft Edge only (verified path); other OSes / browsers
  untested
- Headed mode required for Wiley / ACS supplementary downloads
- SI download is the most fragile code path — main PDFs are reliable
