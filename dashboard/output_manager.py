"""Organizes every application's outputs into
outputs/{Company}/{Job_Title}/{YYYY-MM-DD_HH-MM-SS}/ and writes each
artifact as its own file, so a user can preview/download individual pieces
instead of only the full JSON dump."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from career_copilot.pipeline import PipelineResult


def _sanitize(name: str) -> str:
    """Filesystem-safe folder segment — never trust a company/job-title
    string enough to pass it straight into a path."""
    cleaned = re.sub(r"[^\w\-. ]", "_", name).strip().replace(" ", "_")
    return cleaned or "unknown"


def create_output_folder(company: str, job_title: str, base_dir: str = "outputs") -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder = Path(base_dir) / _sanitize(company) / _sanitize(job_title) / timestamp
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def build_application_artifacts(
    result: PipelineResult,
    *,
    original_resume_text: str,
    original_jd_text: Optional[str],
    metadata: dict,
) -> Dict[str, Tuple[str, str]]:
    """Builds every artifact this application produced, in memory, as
    artifact_name -> (file name, content). Nothing is written to disk here,
    so a public deployment can offer these as downloads without saving them."""
    written: Dict[str, Tuple[str, str]] = {}
    outputs = result.agent_outputs

    written["original_resume"] = ("original_resume.txt", original_resume_text)
    if original_jd_text:
        written["job_description"] = ("job_description.txt", original_jd_text)

    rw = outputs.get("resume_rewrite")
    if rw:
        for version in rw.get("versions", []):
            if not version.get("applicable", True):
                continue
            kind = version.get("version", "version")
            label = str(getattr(kind, "value", kind)).lower().replace(" ", "_")
            written[f"resume_{label}"] = (f"optimized_resume_{label}.md", version.get("full_text", ""))

    ats = outputs.get("ats_optimization")
    if ats:
        written["ats_report_json"] = ("ats_report.json", json.dumps(ats, indent=2))
        written["ats_report_md"] = ("ats_report.md", ats.get("human_readable_summary", ""))

    company_intel = outputs.get("company_intelligence")
    if company_intel:
        written["company_research_json"] = ("company_research.json", json.dumps(company_intel, indent=2))
        written["company_research_md"] = ("company_research.md", company_intel.get("human_readable_summary", ""))

    gap = outputs.get("gap_analysis")
    if gap:
        written["skill_gap_analysis_json"] = ("skill_gap_analysis.json", json.dumps(gap, indent=2))
        written["skill_gap_analysis_md"] = ("skill_gap_analysis.md", gap.get("human_readable_summary", ""))

    assets = outputs.get("application_assets")
    if assets:
        cover_letter = assets.get("cover_letter", {})
        written["cover_letter"] = ("cover_letter.md", cover_letter.get("body", ""))
        written["application_assets_json"] = ("application_assets.json", json.dumps(assets, indent=2))

    interview = outputs.get("interview_coach")
    if interview:
        sections = ["hr_questions", "behavioral_questions", "technical_questions", "product_questions", "company_specific_questions"]
        lines = ["# Interview Questions\n"]
        for section in sections:
            questions = interview.get(section, [])
            if not questions:
                continue
            lines.append(f"\n## {section.replace('_', ' ').title()}\n")
            for q in questions:
                lines.append(f"- **Q:** {q.get('question', '')}")
                if q.get("star_answer"):
                    lines.append(f"  - **Suggested answer:** {q['star_answer']}")
        written["interview_questions"] = ("interview_questions.md", "\n".join(lines))

    learning = outputs.get("learning_certification")
    if learning:
        written["learning_plan_json"] = ("learning_plan.json", json.dumps(learning, indent=2))
        written["learning_plan_md"] = ("learning_plan.md", learning.get("human_readable_summary", ""))

    final_report = outputs.get("final_report")
    if final_report:
        written["final_report_json"] = ("final_report.json", json.dumps(final_report, indent=2))
        written["final_report_md"] = ("final_report.md", final_report.get("human_readable_summary", ""))

    if result.critic_output:
        written["critic_review_json"] = ("critic_review.json", result.critic_output.model_dump_json(indent=2))
    if result.supervisor_output:
        written["supervisor_verdict_json"] = ("supervisor_verdict.json", result.supervisor_output.model_dump_json(indent=2))

    written["full_result_json"] = ("full_result.json", result.model_dump_json(indent=2))
    written["metadata_json"] = ("metadata.json", json.dumps(metadata, indent=2))

    return written


def save_application_outputs(
    folder: Path,
    result: PipelineResult,
    *,
    original_resume_text: str,
    original_jd_text: Optional[str],
    metadata: dict,
) -> Dict[str, str]:
    """Writes every artifact this application produced and returns a dict of
    artifact_name -> file path, for the dashboard's Outputs page to list."""
    artifacts = build_application_artifacts(
        result, original_resume_text=original_resume_text,
        original_jd_text=original_jd_text, metadata=metadata,
    )
    written: Dict[str, str] = {}
    for key, (name, content) in artifacts.items():
        path = folder / name
        path.write_text(content, encoding="utf-8")
        written[key] = str(path)
    return written
