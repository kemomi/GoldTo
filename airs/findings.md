# Findings & Decisions

## Requirements
- Build an MVP for an overseas jewelry strategy simulator Agent
- Primary user is the overseas market strategy analyst
- Core flow is daily brief generation followed by Top 1 event simulation
- Priority capabilities are competitor alerts, compliance reminders, then market opportunities
- Real ingestion is required for competitor official sources and mall/channel official sources
- Industry media and social/KOL inputs can be seeded demo data
- Support Simplified Chinese, Traditional Chinese, and English with original text plus Chinese summary
- Output must stay business-readable, evidence-backed, and safe by default

## Research Findings
- The repository is effectively greenfield: only `.git` and `docs/` exist today
- The approved spec already fixes the product direction, risk policy, and demo mode
- Demo credibility depends on prioritizing real scraped event cases in the showcase path
- Simulation should compare relative business impact, not predict exact prices or sales
- The implementation plan needs a lightweight threshold tuning path because price-change cutoffs are part of the judged demo
- The frontend plan must show three response options and their four-dimension impacts, not just the recommendation

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Use a monorepo-style structure with `apps/api` and `apps/web` | Clean separation while staying simple enough for one-day implementation |
| Use FastAPI for backend orchestration and React/Vite for frontend | Fast startup, explicit APIs, lightweight demo UI |
| Use SQLite plus fixture JSON | Enough persistence and seeded scenario support without extra infrastructure |
| Use rule-first scoring with LLM-assisted extraction/summarization | Matches the spec and avoids unsupported numeric forecasting |
| Keep chat answers deterministic-first | Safer for demo questions than relying fully on live model output |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Planning files did not exist yet | Created project-level planning files before continuing |

## Resources
- Spec: `docs/superpowers/specs/2026-05-23-overseas-jewelry-strategy-simulator-design.md`
- Plan: `docs/superpowers/plans/2026-05-23-overseas-jewelry-strategy-simulator.md`
- Writing plans skill: `C:\Users\test\.codex\superpowers\skills\writing-plans\SKILL.md`
- Planning with files skill: `C:\Users\test\.codex\skills\planning-with-files\SKILL.md`

## Visual/Browser Findings
- No browser artifacts captured in this planning session
