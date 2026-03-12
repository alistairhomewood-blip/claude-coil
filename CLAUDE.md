# Project goal
Build a public web-based coil geometry and magnetic-field tool.

# Non-negotiable rules
- All physics, geometry, units, and magnetic field calculations must live in /physics.
- The UI must never implement or duplicate physics formulas.
- Any physics change must be accompanied by tests or reference-case checks.
- If assumptions are made, state them explicitly before changing code.
- Track units explicitly.
- Always state coordinate system and current direction convention.
- Never silently change sign conventions, units, or geometry definitions.
- If uncertain, stop and explain the uncertainty instead of guessing.
- Screenshots are only supporting context, never the sole source of physics truth.

# Workflow
- Start in plan mode.
- Read relevant files before editing.
- For large changes, produce a plan first.
- After edits, run verification commands and summarize results.
- Keep answers concise and structured.

# Project structure
- /apps/web = UI only
- /physics = physics and geometry logic only
- /tests/reference-cases = known benchmark cases
- /docs/papers = papers
- /docs/notes = extracted equations, conventions, assumptions
- /assets/screenshots = UI screenshots, bug screenshots, diagrams
- /legacy = old prototype code for reference only

# Verification
Before considering a task done:
1. Check for unit consistency
2. Check sign conventions
3. Check coordinate system consistency
4. Check symmetry / limiting cases where applicable
5. Run tests / scripts if available
