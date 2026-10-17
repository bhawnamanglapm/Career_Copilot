"""ASGI entrypoint for hosts that serve Python web apps, such as Vercel.

Locally, use `streamlit run dashboard/app.py` instead.
"""

from pathlib import Path

import streamlit as st

app = st.App(str(Path(__file__).resolve().parent / "dashboard" / "app.py"))
