# Agent Progress Tracking Rule

## Policy
1. **Session Start**:
   - The agent MUST inspect `.state/CURRENT_CONTEXT.md` and `.state/CURRENT_PHASE.md` before taking any actions.
   - The agent must verify existing task progress in `.state/TASK_QUEUE.md`.

2. **Session Execution**:
   - Maintain architectural boundaries: downward dependencies only (`api` -> `services` -> `models`/`database`).
   - Do not bypass schema validation or direct SQL execution outside SQLAlchemy ORM models.

3. **Session End / Milestone Completion**:
   - Update `.state/CURRENT_CONTEXT.md` with what was completed and what remains.
   - Mark completed tasks with `[x]` in `.state/TASK_QUEUE.md`.
   - Update `.state/DEVELOPMENT_STATUS.md` if components or files were created/modified.
   - Record any new design decisions in `.state/DECISIONS.md`.
   - Log any newly discovered bugs or technical debt in `.state/KNOWN_ISSUES.md`.
