"""Public-deployment switch.

Locally, the dashboard is a single-user app: every run is saved to disk and
SQLite so the history pages can show it. On a shared server (for example
Streamlit Community Cloud) that same behaviour would let every visitor read
every other visitor's resume, job description and results, because nothing
is scoped to a session or a login.

Set PUBLIC_DEPLOYMENT=1 on any deployment other people can reach. When it is
on, runs are never written to disk or to the database, the history pages are
turned off, and each visitor downloads their own files straight from the
New Analysis page.
"""

from __future__ import annotations

import os

import streamlit as st

PUBLIC_HISTORY_OFF_MESSAGE = (
    "History is turned off on this public deployment, so visitors can't see each "
    "other's resumes or results. Nothing from your run is saved on the server: "
    "download your files from the **New Analysis** page right after a run."
)


def is_public_deployment() -> bool:
    return os.environ.get("PUBLIC_DEPLOYMENT", "").strip().lower() in ("1", "true", "yes", "on")


def stop_if_public() -> None:
    """Call at the top of any page that reads saved runs."""
    if is_public_deployment():
        st.info(PUBLIC_HISTORY_OFF_MESSAGE)
        st.stop()
