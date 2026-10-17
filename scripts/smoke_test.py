"""Offline smoke test — no ANTHROPIC_API_KEY, no network, no billed calls.

Checks what can be checked without a live model:
  1. Every agent's sample output in outputs/ still matches the agent's output schema.
  2. The full 18-agent pipeline runs end to end in Demo mode with no failed agents.
  3. The dashboard, in Demo mode, runs the bundled sample (not what a visitor typed)
     and, with PUBLIC_DEPLOYMENT=1, writes nothing to disk or the database.

It does NOT check the quality of any live model output; that needs a key and
human review (see career_copilot/evals/).

Run from the repository root:  python scripts/smoke_test.py
"""

from __future__ import annotations

import base64
import importlib
import io
import json
import os
import pkgutil
import re
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

failures: list[str] = []


def check(ok: bool, label: str) -> None:
    print(("PASS " if ok else "FAIL ") + label)
    if not ok:
        failures.append(label)


def check_sample_schemas() -> None:
    import career_copilot.agents as agents_pkg
    from career_copilot.core.demo_client import SAMPLE_FILES

    models = {}
    for module_info in pkgutil.iter_modules(agents_pkg.__path__):
        module = importlib.import_module(f"career_copilot.agents.{module_info.name}")
        for value in vars(module).values():
            if isinstance(value, type) and value.__name__ in SAMPLE_FILES:
                models[value.__name__] = value

    valid = 0
    for model_name, file_name in SAMPLE_FILES.items():
        data = json.loads((REPO / "outputs" / file_name).read_text(encoding="utf-8"))
        try:
            models[model_name].model_validate(data)
            valid += 1
        except Exception as exc:  # noqa: BLE001 — report every invalid sample, not just the first
            print(f"     {file_name}: {str(exc)[:200]}")
    check(valid == len(SAMPLE_FILES) == 18, f"sample outputs match their schemas ({valid}/{len(SAMPLE_FILES)})")


def check_demo_pipeline() -> None:
    from career_copilot.core.demo_client import DemoLLMClient
    from career_copilot.pipeline import PipelineInput, run_pipeline

    events: list[str] = []
    result = run_pipeline(
        PipelineInput(
            candidate_name="Ananya Sharma", target_role="Senior Product Manager — Risk & Fraud",
            resume_text=(REPO / "samples" / "sample_resume.txt").read_text(encoding="utf-8"),
            jd_text=(REPO / "samples" / "sample_jd.txt").read_text(encoding="utf-8"),
            company_name="Razorpay", user_goal="I want a tailored resume, a gap analysis, and interview prep.",
        ),
        on_event=lambda e: events.append(e.event_type),
        client_factory=lambda: DemoLLMClient(outputs_dir=str(REPO / "outputs")),
    )
    completed, failed = events.count("agent_completed"), events.count("agent_failed")
    check(completed >= 15 and failed == 0, f"demo pipeline: {completed} agents completed, {failed} failed")
    check(result.supervisor_output is not None, "demo pipeline: Supervisor verdict produced")


def _dashboard_copy() -> Path:
    """The dashboard writes to paths relative to the working directory, so run
    it from a throwaway copy rather than adding test runs to local history."""
    tmp = Path(tempfile.mkdtemp(prefix="cc_smoke_"))
    for name in ("career_copilot", "dashboard", "samples"):
        shutil.copytree(REPO / name, tmp / name, ignore=shutil.ignore_patterns("*.sqlite3", "__pycache__"))
    (tmp / "outputs").mkdir()
    for f in (REPO / "outputs").glob("*_sample_output.json"):
        shutil.copy(f, tmp / "outputs" / f.name)
    return tmp


def _run_dashboard_demo(public: bool) -> tuple[Path, object]:
    from streamlit.testing.v1 import AppTest

    tmp = _dashboard_copy()
    cwd = os.getcwd()
    os.environ.pop("ANTHROPIC_API_KEY", None)
    if public:
        os.environ["PUBLIC_DEPLOYMENT"] = "1"
    else:
        os.environ.pop("PUBLIC_DEPLOYMENT", None)
    os.chdir(tmp)
    try:
        at = AppTest.from_file(str(tmp / "dashboard" / "app.py"), default_timeout=120)
        at.run()
        run_button = next(b for b in at.button if "Run Pipeline" in b.label)
        run_button.click().run()
    finally:
        os.chdir(cwd)
        os.environ.pop("PUBLIC_DEPLOYMENT", None)
    return tmp, at


def _app_rows(tmp: Path) -> list:
    db_path = tmp / "dashboard" / "career_copilot_dashboard.sqlite3"
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT candidate_name, company_name FROM applications").fetchall()


def check_dashboard() -> None:
    tmp, at = _run_dashboard_demo(public=False)
    try:
        check(not at.exception, "dashboard (local, demo): runs without an exception")
        rows = _app_rows(tmp)
        check(
            len(rows) == 1 and "fictional sample" in rows[0][0] and rows[0][1] == "Razorpay",
            f"dashboard (local, demo): saved under the sample candidate's own name {rows}",
        )
        check(any(tmp.joinpath("outputs").glob("*/*/*/original_resume.txt")), "dashboard (local, demo): output files saved")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tmp, at = _run_dashboard_demo(public=True)
    try:
        check(not at.exception, "dashboard (public, demo): runs without an exception")
        # Hosts such as Vercel have a read-only file system, so public mode must not
        # even create an empty database file.
        check(not (tmp / "dashboard" / "career_copilot_dashboard.sqlite3").exists(),
              "dashboard (public, demo): no database file created")
        saved = [p for p in tmp.joinpath("outputs").iterdir() if p.is_dir()]
        check(saved == [], "dashboard (public, demo): no output folders written")
        check(not (tmp / "career_copilot_runs.sqlite3").exists(), "dashboard (public, demo): no pipeline run log written")
        _check_public_downloads(at)
        _check_public_pages(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _check_public_downloads(at) -> None:
    """Public downloads must be self-contained links: st.download_button files
    live in one server's memory, which fails on multi-instance hosts (Vercel)."""
    check(not at.get("download_button"), "dashboard (public, demo): no server-side download buttons")
    match = next(
        (re.search(r'href="data:[^;"]+;base64,([^"]+)" [^>]*download="career_copilot_results\.zip"', m.value)
         for m in at.markdown if "career_copilot_results.zip" in m.value),
        None,
    )
    names: list[str] = []
    if match:
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(match.group(1)))) as zf:
            names = zf.namelist()
    check("original_resume.txt" in names and len(names) > 10,
          f"dashboard (public, demo): zip packed into its link ({len(names)} files)")


def _check_public_pages(tmp: Path) -> None:
    from streamlit.testing.v1 import AppTest

    cwd = os.getcwd()
    os.environ["PUBLIC_DEPLOYMENT"] = "1"
    os.chdir(tmp)
    try:
        for page in sorted((tmp / "dashboard" / "pages").glob("*.py")):
            at = AppTest.from_file(str(page), default_timeout=60)
            at.run()
            check(not at.exception, f"public page {page.stem}: runs without an exception")
    finally:
        os.chdir(cwd)
        os.environ.pop("PUBLIC_DEPLOYMENT", None)
    check(not (tmp / "dashboard" / "career_copilot_dashboard.sqlite3").exists(),
          "public pages: no database file created")


if __name__ == "__main__":
    check_sample_schemas()
    check_demo_pipeline()
    check_dashboard()
    print(f"\n{len(failures)} failure(s)" if failures else "\nAll checks passed.")
    sys.exit(1 if failures else 0)
