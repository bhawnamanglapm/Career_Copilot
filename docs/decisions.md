# Decision log

> **Draft for the owner to edit.** Each date is the commit date when the decision first appears in this repository.
> The reasons come from commit messages, [LESSONS_LEARNED](portfolio/LESSONS_LEARNED.md), the
> [full PRD](product/PRD.md) and [RISKS](product/RISKS.md). Where a rejected alternative is not recorded anywhere, the
> entry says so instead of guessing.

| Date | Decision | Why | Alternatives / tradeoff | Source |
|---|---|---|---|---|
| 2026-07-10 | **Python, Pydantic and a forced tool call for every agent's output.** | Agents pass typed data to each other, never prose to parse. | Not recorded whether other languages or frameworks were considered. | `6fb61d8`; technical reference "Design decisions" |
| 2026-07-10 | **One narrow agent per job (15 specialists), each built and checked before the next.** | Each agent can be tested on its own, and a reviewer can cross-check one agent against another. | Many model calls per run, so more cost and time than one prompt. | `6fb61d8` to `cce22f2` |
| 2026-07-10 | **Extraction agents re-read the raw resume and posting themselves.** | Keeps them independent, so the Critic can compare their findings instead of trusting one chain. | The same text is read several times. | Technical reference "Design decisions" |
| 2026-07-10 | **Research agents search, then structure in a second call.** | Separates "got the facts wrong" from "got the format wrong"; sourced facts are kept apart from assumptions. | Two calls per research agent. | `6c24520`; LESSONS_LEARNED |
| 2026-07-10 | **Portfolio Recommendation takes the list of gaps, not the resume.** | Its job is to suggest, not to extract, so it builds on Gap Analysis's findings. | Depends on upstream agents being right. | `6edbff1` |
| 2026-07-10 | **"No evidence" is an allowed value in the format.** | Prompt instructions alone didn't stop the model filling gaps with plausible text. | Outputs can look incomplete. | LESSONS_LEARNED; `docs/product/RISKS.md` |
| 2026-07-10 | **One shared registry of agents for the Planner, Critic and Supervisor.** | Separate descriptions in three prompts would drift; a single list can be checked in code. | The registry must be kept in step with the agents by hand. No test fails if they diverge (RISKS). | `422fde5`; LESSONS_LEARNED |
| 2026-07-10 | **The Critic re-adds every number it can check.** | A vague "review for quality" instruction produced near-blanket approval; a mechanical task found a real bug. | Only arithmetic and counts are re-checked this way; other ratings are still model judgement. | `3efdd44`; LESSONS_LEARNED |
| 2026-07-10 | **The Supervisor marks a problem fixed only when a specific fix is named.** | So the verdict doesn't claim more confidence than the system earned. | — | `a4f9097` |
| 2026-07-10 | **Run order comes from the registry, not a fixed sequence.** | Agents run after whatever they depend on in this run. | — | `9353900` |
| 2026-07-10 | **The system drafts; the user sends.** | The person stays responsible for what goes out under their name. | No automation of sending. Listed as a deliberate boundary in the roadmap. | Full PRD, non-goals; product roadmap |
| 2026-07-10 | **Run logging is opt-in; an LLM-judged eval harness is scaffolded.** | So runs can build up a history, and "this agent works" can become a number. | The harness has no cases and no results yet. | `6aea5ab` |
| 2026-07-10 | **A Streamlit dashboard over the pipeline.** | So someone who doesn't write Python can use it. | — | `cbe616e` |
| 2026-07-10 | **Optional passcode for Live mode.** | On a public server anyone with the link could trigger billed calls. | Unset means Live mode is open, as before. | `165b5ea` |
| 2026-07-10 | **Optional hard spend cap per Live run.** | Every agent had its own client, so nothing tracked cost across a run. One shared client now checks the total after every call and stops at the limit. | Work after the cutoff is skipped, including the Critic and Supervisor. | `18737af` |
| 2026-10-18 | **Demo mode replays one fictional candidate and hides uploads.** | It had returned the sample's answer for any upload and saved it under the visitor's name. | Visitors can't try their own resume on the hosted demo. | `e138067` |
| 2026-10-18 | **A switch for public servers: store nothing, turn history off.** | Every visitor could open every other visitor's resume. | No history on a shared server. | `e138067`, `b5dafad` |
| 2026-10-18 | **Rename "Success Rate" to "Marked Ready".** | The number counts runs the Supervisor marked ready, not job-search success. | — | `df439dc` |
| 2026-10-18 | **Remove figures without a source; use reserved contact details in the sample.** | "6–8 hours per role" had no source; the sample's email, phone and LinkedIn looked real. | Older screenshots, the deck and the video still show the old values. | `d9433f5`, `80c1073` |
| 2026-10-18 | **Offline smoke test on every push.** | Keep the formats, run order and privacy honest without a key. | It does not judge the quality of live output. | `48cbbe1` |
| 2026-10-18 | **Host the demo on Vercel, Demo mode only.** | A link anyone can open, with no key on the server. | Live runs could be cut off at the 5-minute limit on the free plan; downloads are packed into their links because Vercel may send requests to a different server. | `bb34e9d`, `2a9d4cc`, `ed1f9f8`, `f4bcff6` |
| 2026-10-19 | **No `evals/` folder until real cases have been run; publish a proposed case set instead.** | Results must come from runs, not estimates. | Quality claims wait for the first run. | This change |

> **OWNER INPUT NEEDED:** add decisions made outside the code, such as why job applications, why a multi-agent
> design rather than one long prompt, why Razorpay as the sample, and anything you tried and dropped.
