# Career Copilot Dashboard

A production-quality Streamlit dashboard for this project's 18-agent
system, and only this project's system — resume optimization, ATS
analysis, company research, gap analysis, interview prep, and career
planning. It is not a generic agent-builder UI.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run dashboard/app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`).

- **Demo mode** (default, no setup needed): runs the bundled fictional
  sample (`samples/sample_resume.txt` and `samples/sample_jd.txt`) through
  the saved `outputs/*_sample_output.json` results instead of calling the
  live API. It does not read uploads, so the upload fields are hidden; every
  demo run shows the same scores and verdict and is saved under the sample
  candidate's name. It lets you exercise the full dashboard, execution
  graph, and history/analytics pages with zero cost and no key.
- **Live mode**: set `ANTHROPIC_API_KEY` before starting Streamlit to unlock
  it — every agent call becomes a real API call.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run dashboard/app.py
```

### Before sharing the URL: turn on `PUBLIC_DEPLOYMENT`

By default every run is saved to `outputs/` and SQLite, and the history
pages (Previous Applications, Companies, Resume Versions, Outputs, History,
Analytics) show every saved run. There are no accounts, so on a shared
server any visitor could open any other visitor's resume and results.

On any deployment other people can reach, set:

```bash
export PUBLIC_DEPLOYMENT=1
```

When it is on, runs are never written to disk or the database, the history
pages show a notice instead of data, and each visitor downloads their own
files (one by one or as a zip) from the New Analysis page. The files live
only in that visitor's browser session. `scripts/smoke_test.py` checks that
a public-mode run writes nothing.

### Gating Live mode behind a passcode

If this app is deployed somewhere public (e.g. Streamlit Community Cloud)
with `ANTHROPIC_API_KEY` set, anyone with the URL can trigger real, billed
API calls — there's no login system. To restrict who can use Live mode,
also set `LIVE_MODE_PASSCODE`:

```bash
export LIVE_MODE_PASSCODE=some-shared-secret
```

When set, selecting Live mode on the home page reveals a passcode field;
the "Run Pipeline" button stays disabled until the correct passcode is
entered. Demo mode is never gated — it's always free to explore. Leaving
`LIVE_MODE_PASSCODE` unset (the default) leaves Live mode ungated, exactly
as before this option existed.

### Capping Live-mode spend

`ANTHROPIC_API_KEY` alone has no built-in spending cap, and a run can hit
Company Intelligence / Learning & Certification / Career Strategy — three
agents that also call Anthropic's billed `web_search` tool on top of normal
token cost. To put a hard ceiling on any single run, set
`LIVE_MODE_COST_LIMIT_USD`:

```bash
export LIVE_MODE_COST_LIMIT_USD=2.00
```

This is an admin-only setting (like `LIVE_MODE_PASSCODE`) — end users never
see or choose it, only whether a run stops. Once set, the pipeline checks
cumulative estimated cost after every single agent call during a Live run;
the moment it's met or exceeded, execution stops immediately — no further
agents, no Critic, no Supervisor, since those would themselves spend more.
The dashboard shows a clear "Stopped early" banner with the amount spent,
and whatever agents did complete before the cutoff are still saved to the
output folder. If the model in use isn't in `core/pricing.py`'s pricing
table (cost can't be computed), the run fails safe and stops rather than
accumulating untracked spend. Demo mode is never subject to this limit —
it never calls the billed API in the first place. Leaving
`LIVE_MODE_COST_LIMIT_USD` unset (the default) leaves Live-mode runs
uncapped, exactly as before this option existed.

### Deploying on Vercel

The repository includes the two files Vercel needs:

- `asgi.py` serves the dashboard as a Python web app (Streamlit's `st.App`,
  which needs Streamlit 1.66 or later).
- `vercel.json` sets the time limit to 300 seconds and leaves docs, scripts
  and CI files out of the bundle.

To deploy, import the GitHub repository in the Vercel dashboard (framework
preset: Other) and set these environment variables before the first deploy:

| Variable | Value | Needed for |
|---|---|---|
| `PUBLIC_DEPLOYMENT` | `1` | Always. Vercel's file system is read-only, and without this visitors would also share history. |
| `ANTHROPIC_API_KEY` | your key, marked **Sensitive** | Live mode only |
| `LIVE_MODE_PASSCODE` | a passcode you share privately | Live mode only. Without it, anyone with the link can spend your API credit. |
| `LIVE_MODE_COST_LIMIT_USD` | e.g. `2.00` | Live mode only |

Leave out `ANTHROPIC_API_KEY` for a Demo-only site.

Known risks on Vercel. These come from Vercel's documentation and have not
yet been seen in a real deployment of this app:

- **Live runs may be cut off.** Streamlit keeps a WebSocket open for the whole
  session. Vercel closes it at the function's time limit: 300 seconds on the
  Hobby plan (up to 800 on Pro). A Live run calls up to 18 agents in turn,
  some with web search, and no Live run has been timed yet. A run cut off
  partway has still spent API credit. `LIVE_MODE_COST_LIMIT_USD` caps money,
  not time.
- **Sessions can reset.** WebSocket support on Vercel is in beta. If the
  browser reconnects to a different server instance, the visitor's results
  and download buttons are gone and they must run again.

If either becomes a problem, Streamlit Community Cloud runs the same app
(`dashboard/app.py`) on a long-running server without these limits.

## What's dynamic vs. what's fixed

**Dynamic — no code change needed when agents change:** `dashboard/discovery.py`
scans `career_copilot/agents/*.py` at every page load (or on demand via the
"Rescan agents" button on the Settings page) and reads each agent's real
`input_model`/`output_model` fields directly off the class. The 15
specialist agents' category/description/requires/depends_on come from
`career_copilot/core/registry.py` (itself a data file, not code); the 3
orchestration agents' `depends_on` is derived structurally — any input field
named `<other_agent_id>_output` becomes a dependency edge — so it never
needs a hardcoded list either. Add a new `career_copilot/agents/foo.py`
defining a `BaseAgent` subclass and it appears in the execution graph,
Settings' agent catalog, and (once wired into `career_copilot/pipeline.py`'s
`_build_input`) the live run, without touching any dashboard file.

**Fixed by design, not by omission:** the dashboard only ever shows agents
that exist in `career_copilot/agents/` — it has no concept of a generic
agent framework, workflow templates, or non-Career-Copilot agents. That's
the point: this is Career Copilot's dashboard, not an "AI Builder OS."

## Architecture

```
dashboard/
  app.py                   # New Analysis (home page): upload, run, live monitor, console
  discovery.py               # Dynamic agent discovery — see above
  db.py                       # SQLite: applications, companies, resume_versions, execution_logs
  file_parsing.py             # PDF/DOCX/TXT -> text
  output_manager.py           # outputs/{Company}/{Job_Title}/{timestamp}/ folder + per-artifact files
  privacy.py                  # PUBLIC_DEPLOYMENT switch: no saving, history pages off
  graph_layout.py             # Topological layered layout for the execution DAG
  components/
    cards.py                  # Summary metric cards
    execution_graph.py        # Plotly DAG renderer, colored by live status
    activity_console.py       # Filterable/searchable live log table
  pages/
    1_Previous_Applications.py  # History table + resume comparison
    2_Companies.py               # Per-company research profiles, reused across applications
    3_Resume_Versions.py         # All resume versions + ATS score chart
    4_Outputs.py                  # Browse/preview/download every artifact per application
    5_History.py                  # Full per-agent execution log across every run
    6_Analytics.py                 # Applications by month, ATS trends, industries, missing skills
    7_Settings.py                   # API key status, DB export, live discovered-agent catalog

career_copilot/
  core/demo_client.py    # DemoLLMClient — per-instance sample-output replay (no monkeypatching,
                          # safe for a multi-session Streamlit server)
  pipeline.py             # run_pipeline() gained two new optional params for this dashboard:
                           #   on_event: Callable[[ExecutionEvent], None] — live progress callback
                           #   client_factory: Callable[[], LLMClient] — swap in DemoLLMClient
                           # Both are additive; nothing that called run_pipeline() before needs to change.
```

## Database

SQLite at `dashboard/career_copilot_dashboard.sqlite3` (gitignored — created
on first run by `db.init_db()`). Four tables: `applications`, `companies`,
`resume_versions`, `execution_logs`. Every page in `pages/` reads from this
one database; `app.py` is the only writer, at the end of each pipeline run.
CSV/Excel export is available from the History and Settings pages.

This is separate from `career_copilot/core/run_log.py`'s `RunLogger`
(`career_copilot_runs.sqlite3`), which the dashboard also writes to via
`run_pipeline(logger=...)` — that one is the generic, dashboard-independent
pipeline run log described in the main project README; this dashboard's
schema is richer and specific to the UI (companies, resume versions,
per-agent execution logs, output folder tracking).

## Output folder layout

```
outputs/
  {Company_Name}/
    {Job_Title}/
      {YYYY-MM-DD_HH-MM-SS}/
        original_resume.txt
        job_description.txt
        optimized_resume_{ats,recruiter,startup,enterprise}.md   (whichever versions applied)
        ats_report.{json,md}
        company_research.{json,md}
        skill_gap_analysis.{json,md}
        cover_letter.md
        application_assets.json
        interview_questions.md
        learning_plan.{json,md}
        final_report.{json,md}
        critic_review.json
        supervisor_verdict.json
        full_result.json       # the complete PipelineResult
        metadata.json
```

## Known limitations

- Agent discovery re-scans on each Streamlit rerun within a session (Python
  import caching keeps this cheap) and via the explicit "Rescan agents"
  button in Settings; it does not watch the filesystem for changes while
  the server is idle — restart the app or click Rescan after adding/removing
  an agent module.
- Live-mode cost/token estimates use Anthropic's list pricing
  (`career_copilot/core/pricing.py`); Demo-mode token counts are a rough
  chars/4 approximation, always labeled "(demo, approximate)."
- The dashboard is a single-process local app (`streamlit run`), not a
  deployed multi-tenant service. There are no user accounts: history is
  either shared by everyone (default) or turned off (`PUBLIC_DEPLOYMENT=1`).
  Per-user history would need logins and per-user storage.
