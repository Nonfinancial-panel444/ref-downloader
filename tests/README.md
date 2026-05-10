# Manual smoke-test recipe

This project has no automated test suite yet. Before submitting a PR, run a
manual smoke test for the publisher you touched.

## Per-publisher smoke test

Pick a sample DOI for the publisher (suggestions in
[../docs/SUPPORTED_PUBLISHERS.md](../docs/SUPPORTED_PUBLISHERS.md)) and run:

```powershell
python run_ref_downloader.py <PARENT_DOI_THAT_CITES_YOUR_PUBLISHER> --output-dir test_smoke
```

Watch the console for refs in your target publisher:

| Status | Meaning |
|---|---|
| `downloaded (X KB)` | success — PDF saved |
| `already_exists` | previously downloaded, skipped |
| `manual_pending (...)` | needs human / paywall / SSO |
| `failed (...)` | automatic download failed |
| `ignored` | listed in `[institution].ignored_access_dois` |

For deeper inspection, open
`test_smoke/<project>/runs/<timestamp>-round-03/events.jsonl` and grep for
your publisher / DOI / failure reason.

Clean up after testing:

```powershell
Remove-Item -Recurse -Force test_smoke
```

## Empty-config smoke test

This verifies the wrapper still runs against vanilla open-internet defaults
(no `config.local.toml`):

```powershell
Move-Item config.local.toml config.local.toml.bak
python run_ref_downloader.py 10.1021/jacs.5c05017 --output-dir test_smoke
Move-Item config.local.toml.bak config.local.toml
```

Expected:
- Console prints `WARNING: crossref.mailto is the placeholder.`
- `extract_refs.py` succeeds (Crossref reachable without auth)
- `validate_refs.py` succeeds (per-DOI metadata fetch works)
- `download_refs.py` may or may not succeed for individual refs — paywalled
  refs without institutional access will paywall, that's acceptable

What MUST NOT happen:
- `ImportError` / `NameError` / `AttributeError` traceable to `_config.py`
- `KeyError` / `NoneType` from a missing config field
- Personal paths (e.g. `C:\Users\<you>\...`) appearing in any traceback

## Quick import-only check

If you've changed structure and want to verify without running a full
download:

```powershell
python -c "import _config, run_ref_downloader, extract_refs, validate_refs, download_refs; print('imports OK')"
```

This catches `SyntaxError`, `ImportError`, `NameError` early.

## Future automated tests

When pytest scaffolding lands, target:

- `_config.py`: TOML merge order, env override behavior, missing files
- `extract_refs.py`: argument parsing, non-tty input handling
- `download_refs.py` (unit-testable parts only): URL construction, status
  classification, label generation

Network-dependent integration tests (Crossref, Edge automation) likely stay
manual or behind an opt-in marker.
