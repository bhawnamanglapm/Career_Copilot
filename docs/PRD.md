# Career Copilot PRD: where the prototype stands

> **Draft for the owner to edit.** The full PRD is [docs/product/PRD.md](product/PRD.md). It was written on 10 Jul 2026,
> during the build. This page checks each of its requirements against the code and the sample outputs, as of
> 19 Oct 2026. It adds no new requirements. **No success metric in the PRD has been measured.**

## Summary

Given a resume, a job posting and a company name, produce a full application package (gap analysis, ATS check,
tailored resume versions, company research, interview prep, outreach drafts) where every claim traces back to the
inputs or a cited source, then give a ready / not-ready verdict.

**Users** (from the PRD): job seekers applying to specific roles; career changers who want an honest read on where
they stand; people studying multi-agent design. **No users are recorded.**

## Functional requirements

| ID | Requirement (short) | Status | Evidence |
|---|---|---|---|
| FR1 | Gap analysis, ATS score and at least one tailored resume for a resume and posting | **Built.** Shown on one fictional sample. Like all 18 samples, it was written during the build by following the agents' prompts, not produced by the pipeline calling the API. | `outputs/gap_analysis_*`, `ats_optimization_*`, `resume_rewrite_*` |
| FR2 | Company-specific content grounded in live, cited research, never invented | **Built** (search, then a separate structuring call). The sample cites public news about Razorpay; the sources were not re-checked. The commit that added it (`6c24520`) says the sample came from a real run; no run log confirms it. | `career_copilot/agents/company_intelligence.py` |
| FR3 | Every agent's output validates against a declared schema | **Built and tested.** | Smoke test: 18 of 18 samples match, in CI |
| FR4 | Can say "insufficient evidence" or leave a field empty instead of inventing | **Built** into the schemas. Seen in the sample: Interview Coach gives no story for the mentoring question and notes that the resume has no example. Not measured. | Agent schemas; `outputs/interview_coach_*` |
| FR5 | A review layer catches inconsistencies before a deliverable counts as ready | **Built**, not run against the API. A review of the samples written by following the Critic's prompt caught one real bug: a learning-plan total that didn't match its own line items. | `outputs/critic_sample_output.md` |

## Non-functional requirements

| Requirement | Status |
|---|---|
| Non-fabrication is the top priority, enforced by structure as well as instructions | Enforced in the schemas and checked by the Critic. **The rate of invented claims has not been measured.** |
| Cost and latency: the Planner's estimate should reflect that research agents cost most | The Planner gives an estimate. A hard spend cap was added later (see below). **No real cost or time has been recorded**, since there are no recorded Live runs. |
| Output structure is always valid, even though wording varies | Enforced by the schemas; tested on the samples. |

## Added since the PRD

Built in July and October 2026, not in the original PRD:

| Feature | Why | Commit |
|---|---|---|
| Streamlit dashboard with run history | So someone who doesn't write Python can run it (a v0.2 roadmap item) | `cbe616e` |
| Optional passcode for Live mode | Anyone with the link could otherwise trigger billed calls | `165b5ea` |
| Optional hard spend cap per Live run | Stops the run as soon as estimated cost reaches the limit | `18737af` |
| Honest Demo mode | It replays one fictional candidate and hides the upload fields | `e138067` |
| Public-deployment switch | On a shared server nothing is stored and history is off | `e138067`, `b5dafad` |
| Offline smoke test in CI | Checks formats, run order and privacy without a key | `48cbbe1` |
| Hosted demo on Vercel | A link anyone can open | `bb34e9d` to `f4bcff6` |

## Success metrics

The PRD names hallucination rate, accuracy on hard facts, completeness, cost per full run and, once there are users,
time saved and interview or offer rate. **None has been measured.** A proposed first eval set is in the
[README](../README.md#how-i-measured-quality).

> **OWNER INPUT NEEDED:** the target for each metric. For example: what rate of invented claims would be acceptable
> before you'd let a real job seeker use it?

## Open questions

From the PRD, still open:
1. Should the system ever send anything on the user's behalf? Current design: no, it only drafts.
2. Should there be a "should you even apply?" check before the full pipeline runs on a clear mismatch?

> **OWNER INPUT NEEDED:** your answers, and anything you'd add after the October review.
