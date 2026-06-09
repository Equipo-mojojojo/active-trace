---
name: openspec-apply-change
description: Implement tasks from an OpenSpec change. Use when the user wants to start implementing, continue implementation, or work through tasks.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.3.1"
---

Implement tasks from an OpenSpec change.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

0. **Cargar skills de dominio y preparar herramientas visuales** ← OBLIGATORIO ANTES DE CODEAR

   **0.1 Identificar el dominio del change** (leer el nombre y el `proposal.md` si existe):

   | Dominio del change | Skills a cargar (leer el SKILL.md antes de escribir código) |
   |--------------------|--------------------------------------------------------------|
   | Frontend (C-21 a C-24, cualquier `frontend-*` o `ui-*`) | `typescript-advanced-types`, `tailwind-design-system`, `playwright-best-practices`, `dashboard-crud-page` |
   | Backend Core (modelos, routers, migraciones, auth) | `fastapi-templates`, `postgresql-table-design`, `python-testing-patterns`, `test-driven-development` |
   | Backend Aux (seguridad, integraciones, performance) | `api-security-best-practices`, `postgresql-optimization`, `systematic-debugging` |
   | DevOps (Docker, infra) | `multi-stage-dockerfile` |

   Leer cada SKILL.md relevante desde `.agents/skills/<nombre>/SKILL.md` ANTES de escribir código.

   **0.2 Si el change es de frontend → usar Stitch MCP para generar referencia visual**

   Antes de escribir JSX, generar las pantallas principales del change con Stitch:
   ```
   mcp__stitch__generate_screen_from_text (project_id: "17067148584640101066")
   ```
   Generar UNA pantalla por vista principal del change (ej: login, dashboard, tabla de atrasados).

   **Reglas de uso de Stitch — INAMOVIBLES:**
   - Stitch es SOLO referencia visual: layout, colores, tipografía, espaciado, componentes UI.
   - NUNCA usar el código generado por Stitch directamente — solo inspeccionar visualmente.
   - NUNCA inferir modelos de datos, nombres de campos, tipos ni estructuras de BD desde Stitch.
   - NUNCA conectar Stitch a endpoints ni al backend. Stitch no sabe nada del dominio.
   - Los tipos, schemas y estructuras de datos vienen SIEMPRE de los specs OpenSpec y la KB del proyecto.
   - El código real se escribe desde cero siguiendo las skills de dominio y las convenciones del proyecto.

   **0.3 Verificar que Stitch esté disponible** (solo frontend):
   - Si `mcp__stitch__*` no está disponible: continuar sin él y documentar en el resumen que Stitch no fue usado.
   - Si está disponible: obligatorio usarlo antes de cualquier componente de UI.

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **AskUserQuestion tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., `/opsx:apply <other>`).

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns:
   - `contextFiles`: artifact ID -> array of concrete file paths (varies by schema - could be proposal/specs/design/tasks or spec/tests/implementation/docs)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest using openspec-continue-change
   - If `state: "all_done"`: congratulate, suggest archive
   - Otherwise: proceed to implementation

4. **Read context files**

   Read every file path listed under `contextFiles` from the apply instructions output.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI

6. **Implement tasks (loop until done or blocked)**

   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - Mark task complete in the tasks file: `- [ ]` → `- [x]`
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts

7. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: suggest archive
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

All tasks complete! Ready to archive this change.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- **NUNCA escribir código sin haber leído las skills de dominio del paso 0**
- **NUNCA escribir JSX/componentes de frontend sin haber generado la referencia visual en Stitch (paso 0.2)**
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- Update task checkbox immediately after completing each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
