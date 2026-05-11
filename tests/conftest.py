"""pytest configuration: put the skill's scripts dir on sys.path so tests can
import the top-level modules (`_config`, `extract_refs`, `validate_refs`,
`run_ref_downloader`) directly.

After the Level-2 restructure the skill lives at `skills/ref-downloader/`
and its Python sources live at `skills/ref-downloader/scripts/`. Tests stay
at the repo's `tests/` directory; this conftest just patches sys.path to
reach the scripts.

`download_refs.py` is intentionally NOT imported by the test suite — its
module-level `from playwright.async_api import ...` would force `playwright`
as a hard test dependency. Browser-driven behavior is covered by the manual
smoke recipe in `tests/README.md`.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / "skills" / "ref-downloader" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
