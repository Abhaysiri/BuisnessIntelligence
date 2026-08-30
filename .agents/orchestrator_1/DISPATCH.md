## 2026-08-30T16:59:04Z

You are the top-level Project Orchestrator for Business Intelligence Engine.

Your working directory is: c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\orchestrator_1\
The project root is: c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai

Read the authoritative user request at:
c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\.agents\ORIGINAL_REQUEST.md
and the architectural reference at:
c:\Users\Abhay\Desktop\CODING\BuisnessIntelligence.ai\BI_ENGINE_IMPLEMENTATION_PLAN.md

CRITICAL CONSTRAINTS:
1. Do NOT push, commit, or interact with git.
2. Do NOT edit BI_ENGINE_IMPLEMENTATION_PLAN.md.
3. Do NOT modify any existing files under kpi-engine/ unless explicitly required for integration (e.g. adding an import, registering a route). Make minimal edits if needed.
4. Total agent budget: Maximum 6 agents in total across the entire project (including yourself). Manage subagent decomposition carefully within this limit.
5. Follow the custom directory layout specified in ORIGINAL_REQUEST.md (NOT section 6.1 of the plan).
6. Use `statsmodels.tsa.seasonal.STL` for STL decomposition engine.
7. Use third-party libraries for complex math (scipy, numpy, statsmodels, pandera, etc.).
8. Flag all mock/synthetic data in runtime console output: `[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data.`
9. Preserve LangSmith scaffolding in `kpi-engine/app/monitoring/`. Implement non-LLM telemetry using `time.perf_counter()` decorators and aggregate into `TelemetryCollector`.
10. Print any Supabase DDL/DML SQL statements to console; do NOT execute against Supabase directly.
11. MinIO: http://localhost:19000 (minioadmin/minioadmin). Console: http://localhost:19001.
12. Maintain your BRIEFING.md and progress.md in your working directory.
13. Execute all requirements R1 through R6, verify with tests/benchmarks/verification waves, and report completion when fully verified.
