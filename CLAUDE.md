# CLAUDE.md — SAP EPM Design Agent

> Read this file completely before writing, editing, or refactoring any code.
> All implementation decisions must align with the rules stated here.
> When in doubt: check the FSD at docs/SAP_EPM_Design_Agent_FSD.md first.

---

## 1. Project Identity

| Field | Value |
|---|---|
| App Name | SAP EPM Design Agent |
| Version | 2.1 |
| Type | Streamlit Web Application |
| AI Engine | Anthropic Claude API (anthropic Python SDK) |
| Python Version | 3.11+ |
| FSD Reference | docs/SAP_EPM_Design_Agent_FSD.md |

---

## 2. Canonical Folder Structure

```
sap_epm_design_agent/
│
├── app.py                            # Streamlit entry point — UI only
├── CLAUDE.md                         # This file
├── .env                              # Credentials and config (never commit)
├── .env.example                      # Safe-to-commit template
├── requirements.txt
├── README.md
├── docs/
│   └── SAP_EPM_Design_Agent_FSD.md
│
├── core/
│   ├── __init__.py
│   ├── llm_client.py                 # ONLY file that calls Anthropic SDK
│   ├── brd_parser.py                 # PDF + DOCX text extraction
│   ├── brd_summariser.py             # Pre-summarisation → structured dict
│   ├── question_engine.py            # Clarification question generation
│   ├── fsd_generator.py              # FSD batch generation orchestration
│   ├── tsd_generator.py              # TSD batch generation orchestration
│   ├── section_regenerator.py        # Single-section regeneration
│   ├── interactive_generator.py      # Single-section generate/review/refine/lock loop
│   └── document_builder.py           # python-docx assembly — named styles only
│
├── skills/
│   ├── __init__.py                   # Registry + load functions
│   ├── sap/
│   │   ├── __init__.py
│   │   ├── bw4hana.py                # BW/4HANA specific knowledge
│   │   ├── bw_on_hana.py             # BW 7.5 on HANA knowledge
│   │   ├── sac_analytics.py          # SAC Analytics knowledge
│   │   ├── sac_planning.py           # SAC Planning / FP&A knowledge
│   │   ├── bpc.py                    # BPC Standard + Embedded knowledge
│   │   ├── group_reporting.py        # Group Reporting knowledge
│   │   ├── papm.py                   # PaPM knowledge
│   │   ├── bdc.py                    # BDC / Datasphere knowledge
│   │   ├── embedded_analytics.py     # CDS / Fiori knowledge
│   │   └── abap.py                   # ABAP knowledge
│   └── domain/
│       ├── __init__.py
│       ├── finance.py
│       ├── sales.py
│       ├── procurement.py
│       ├── operations.py
│       └── hr.py
│
├── prompts/
│   ├── base_system.j2
│   ├── brd_summarisation.j2          # Pre-summarisation prompt
│   ├── brd_analysis.j2               # Clarification questions
│   ├── fsd_generation_batch.j2       # Batch FSD section generation
│   ├── tsd_generation_batch.j2       # Batch TSD section generation
│   └── section_regeneration.j2       # Single section regeneration
│
├── templates/
│   ├── fsd_default_structure.py
│   └── tsd_default_structure.py
│
├── utils/
│   ├── __init__.py
│   ├── file_handler.py               # Upload validation, multi-file handling
│   ├── session_state.py              # Session state keys + step constants
│   └── jinja_env.py                  # Shared Jinja2 environment factory
│
└── tests/
├── test_brd_parser.py
├── test_brd_summariser.py
├── test_question_engine.py
├── test_fsd_generator.py
├── test_tsd_generator.py
└── test_document_builder.py
```

---

## 3. Architectural Rules — NEVER VIOLATE

### 3.1 Layer Separation
- `app.py` contains ONLY Streamlit UI: widgets, layout, session state, calls to `core/`
- `app.py` NEVER calls the Anthropic SDK directly
- `core/` modules contain business logic ONLY — no Streamlit imports, no UI calls
- `skills/` modules return pure knowledge dicts — no LLM calls, no file I/O
- `prompts/` contains Jinja2 `.j2` templates ONLY — no Python logic

### 3.2 LLM Client Contract
- `core/llm_client.py` is the ONLY file that imports `anthropic`
- All LLM calls go through `call_llm(prompt, system, max_tokens) -> str`
- Retry logic (max 3, exponential backoff) is implemented in `llm_client.py`
- API key and base URL loaded from `.env` — never hardcoded

### 3.3 Jinja2 Environment
- A single shared Jinja2 `Environment` instance is created in `utils/jinja_env.py`
- All `core/` modules import `get_jinja_env()` from `utils/jinja_env.py`
- NEVER create a new `Environment(loader=FileSystemLoader(...))` inside a core module
- This was duplicated in 3 files in v1 — do not repeat that mistake

### 3.4 Prompt Management
- All prompt text lives in `prompts/` as `.j2` files — NEVER as Python strings or f-strings
- Templates use `{{ variable }}` for injection, `{% if %}` for conditional sections
- Each template has a header comment block: purpose, input variables, output format
- System prompt = `base_system.j2` (always) + skill variables injected

### 3.5 Skills Architecture
- Each SAP technology has its own dedicated skill file in `skills/sap/`
- Every skill file implements `get_knowledge() -> dict` with keys:
  `summary`, `key_concepts`, `kpis`, `sap_objects`, `common_patterns`
- SAP_SKILL_REGISTRY in `skills/__init__.py` maps each technology dropdown value
  to exactly one skill file's `get_knowledge` function
- Each technology maps to its OWN dedicated skill — no two technologies share a skill
- Domain skills are loaded selectively based on auto-detected domains from BRD summary
  — NOT all domains loaded every time

### 3.6 Document Builder Contract
- `core/document_builder.py` owns ALL python-docx logic
- `fsd_generator.py` and `tsd_generator.py` call document_builder — they never
  import or use python-docx directly
- ALL formatting uses named Word styles — NEVER inline font size, colour, or bold overrides
- Named styles must be defined/registered in the document at creation time:
  `EPM Heading 1`, `EPM Heading 2`, `EPM Heading 3`, `EPM Body Text`,
  `EPM Table Header`, `EPM Table Body`, `EPM Code Block`, `EPM Bullet`, `EPM Caption`
- Cover page is always generated as page 1
- Table of Contents is always page 3 (Word auto-field, not static text)
- Alternating row shading on all tables: white / #D6E4F0

### 3.7 Generation Architecture — Interactive Section Loop (default)
- FSD and TSD are NEVER generated in a single LLM call
- The default generation mode as of v2.1 generates **exactly one section per LLM call**
- Each call receives: structured_summary + technology_context + **all previously locked
  sections' content and Q&A** + the single target section's spec
- A section is not "generated" in the sense of being final until the user explicitly
  approves it (blank/confirm response) — until then, it is a draft subject to
  regeneration with feedback folded in
- `interactive_generator.py` owns this loop: `generate_section_draft()`,
  `apply_feedback_and_regenerate()`, `lock_section()`
- Locked section state (content + Q&A history + revision count) is stored in session
  state, keyed by section number, and passed forward to every subsequent section's prompt
- Maximum regeneration attempts per section: `MAX_SECTION_REGENERATION_ATTEMPTS` in
  .env (default 5). If exceeded, the section is force-locked using the latest draft and
  flagged in the Open Questions Register
- Failed generation calls are retried independently (via `llm_client.py`) — locked
  sections are never discarded or regenerated as a side effect of a later failure
- Final document is assembled from the locked-sections dict once every section is locked
- The legacy adaptive batching approach (grouping multiple sections into one call via
  `SECTION_WEIGHT` / `_BATCH_QUOTA` in `fsd_generator.py`/`tsd_generator.py`) remains in
  the codebase as an optional fallback "fast mode" only, gated behind
  `INTERACTIVE_GENERATION=false` in .env — it must never run concurrently with the
  interactive loop for the same document

### 3.8 BRD Pre-Summarisation Contract
- `core/brd_summariser.py` performs the pre-summarisation LLM call
- Input: raw_brd_text + concatenated supporting docs + discussion notes
- Output: structured dict with keys:
  `requirements`, `kpis`, `data_sources`, `domain`, `key_entities`, `open_gaps`
- This dict — NOT raw BRD text — is passed to ALL subsequent LLM calls
- Raw BRD text is NEVER passed to FSD or TSD generation prompts

### 3.8a Interactive Section Loop Contract
- `core/interactive_generator.py` is the only module allowed to orchestrate the
  generate → present → review → lock cycle
- Each section generation call must include **one and only one** target section in the
  prompt — never multiple sections per call while this mode is active
- A section carries a status of exactly one of: `pending`, `current`, `locked`
- `locked_sections: dict` in session state stores, per section number: final content,
  the targeted question asked (if any), the user's answer/correction text, and a
  revision count
- The targeted question is generated as part of the same call that drafts the section
  content — never a separate call
- `app.py` renders section status from `locked_sections` and the current section's live
  draft — it must not track duplicate state of its own
- Maximum 1 targeted question per section per generation attempt — no multi-question
  batches inside the interactive loop

### 3.9 Two-Phase Workflow Contract
- Phase 1 (FSD) and Phase 2 (TSD) are separate, sequential workflow stages
- Phase 2 NEVER starts until Phase 1 FSD download is available
- TSD generation receives the FULL parsed FSD text as input — not a summary string
- User can provide FSD via session state OR by re-uploading a .docx
- Both paths go through the same `parse_brd()` function in `brd_parser.py`

---

## 4. Environment Variables

```env
# .env.example — copy to .env and fill in values
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_BASE_URL=                        # Optional: Capgemini internal gateway URL
CLAUDE_MODEL=claude-sonnet-4-6
MAX_TOKENS_SUMMARISE=2000
MAX_TOKENS_QUESTIONS=1500
MAX_TOKENS_BATCH=4000
GENERATION_BATCH_SIZE=3
MAX_FILE_SIZE_MB=50
APP_TITLE=SAP EPM Design Agent
INTERACTIVE_GENERATION=true                # false reverts to legacy batched blind generation
MAX_SECTION_REGENERATION_ATTEMPTS=5
```

---

## 5. Scalability Patterns

### Adding a New SAP Technology
1. Create `skills/sap/<technology>.py`
2. Implement `get_knowledge() -> dict` with keys:
   `summary`, `key_concepts`, `kpis`, `sap_objects`, `common_patterns`
3. Register in `skills/__init__.py` under `SAP_SKILL_REGISTRY` with the exact
   dropdown string as the key
4. Add dropdown string to `SAP_TECHNOLOGIES` list in `utils/session_state.py`
5. ✅ Zero changes to `core/`, `prompts/`, or `app.py`

### Adding a New Domain Skill
1. Create `skills/domain/<domain>.py`
2. Implement `get_knowledge() -> dict`
3. Register in `skills/__init__.py` under `DOMAIN_SKILL_REGISTRY`
4. ✅ Auto-detection in `brd_summariser.py` picks it up automatically

### Adding a New Output Document Type (e.g. Test Script)
1. Create `core/test_script_generator.py` — follow `fsd_generator.py` pattern exactly
2. Create `prompts/test_script_generation_batch.j2`
3. Add section schema to `templates/test_script_default_structure.py`
4. Add Phase 3 UI panel and download button to `app.py`
5. ✅ Zero changes to existing generators

### Modifying Prompt Behaviour
1. Edit the relevant `.j2` file in `prompts/` — no Python changes
2. Run `pytest tests/ -v` after changes

---

## 6. Coding Standards

### Python
- All functions: type hints + one-line docstring
- No function longer than 40 lines — decompose if needed
- All exceptions caught at `core/` layer, surfaced to `app.py` as clean error strings
- Use `logging` module throughout — never `print()`
- Log level: `INFO` for normal flow, `WARNING` for recoverable issues, `ERROR` for failures

### Streamlit UI (`app.py`)
- Session state keys are CONSTANTS in `utils/session_state.py` — never raw strings
- Workflow steps are numbered constants: `STEP_UPLOAD`, `STEP_SELECT_TECHNOLOGY`, etc.
- Phase 1 and Phase 2 are clearly labelled sections in the UI
- Every LLM call shows `st.spinner()` with a descriptive label including section numbers
- Multi-step generation uses `st.status()` with per-batch progress updates
- Section regeneration uses a `st.selectbox` listing section numbers + titles
- The step navigator (left panel) renders section status (locked / current / pending)
  from `locked_sections` and the active section pointer only — never inferred from
  document byte content
- Every regeneration triggered by user feedback shows `st.spinner()` labelled with the
  section name and current attempt count (e.g. "Refining Section 5 — attempt 2 of 5")

### Document Builder
- Named styles are registered once at document creation in `_register_epm_styles(doc)`
- All text application uses `para.style = doc.styles["EPM Body Text"]` pattern
- NEVER use `run.font.size = Pt(10)` — use the named style instead
- Tables always call `_apply_table_styles(table)` after creation

### Jinja2 Prompts
- Templates document their variables in the header `{# ... #}` comment block
- No business logic in templates — conditional logic uses simple `{% if %}` only
- Batch generation templates receive `batch_sections` as a list of section dicts

---

## 7. Data Flow (End-to-End)

```
PHASE 1
[Upload: BRD + Supporting Docs + Discussion Notes + Metadata]
→ file_handler.py: validate each file, read bytes
→ brd_parser.py: extract text from each file
→ concatenate with === DOCUMENT: filename === delimiters
[Pre-Summarisation]
→ brd_summariser.py: build prompt from brd_summarisation.j2
→ llm_client.py: API call → structured_summary dict
→ domain auto-detection from structured_summary["domain"]
→ store structured_summary in session state
[Clarification Questions]
→ question_engine.py: build prompt from brd_analysis.j2
inject: structured_summary + sap_skill + domain_skills
→ llm_client.py: API call → JSON question list
→ display in app.py
[FSD Generation — Batched]
→ fsd_generator.py: for each batch of 3 sections:
build prompt from fsd_generation_batch.j2
inject: structured_summary + sap_skill + domain_skills + answers + batch_sections
llm_client.py: API call → section content
store in section_content_dict
→ document_builder.py: assemble .docx with named styles, cover page, TOC
→ store FSD bytes in session state + display download button
[Section Regeneration — Optional]
→ section_regenerator.py: build prompt from section_regeneration.j2
inject: structured_summary + existing section titles + target section spec
→ llm_client.py: API call → single section content
→ document_builder.py: rebuild document with replacement section
PHASE 2
[FSD Input]
→ Option A: use FSD bytes from session state
→ Option B: re-upload .docx → brd_parser.py extracts full text
→ fsd_full_text stored in session state
[TSD Generation — Batched]
→ tsd_generator.py: for each batch of 3 sections:
build prompt from tsd_generation_batch.j2
inject: structured_summary + fsd_full_text + sap_skill + domain_skills
+ answers + batch_sections
llm_client.py: API call → section content
store in section_content_dict
→ document_builder.py: assemble .docx with named styles, cover page, TOC
→ display download button
```

---

## 8. What Claude Code Must Never Do

- ❌ Call `anthropic.Anthropic()` anywhere except `core/llm_client.py`
- ❌ Write prompt text as Python strings or f-strings — use `.j2` templates
- ❌ Import `streamlit` in any file inside `core/` or `skills/`
- ❌ Store API keys, model names, or batch sizes as code constants — use `.env`
- ❌ Add business logic to `app.py`
- ❌ Add UI logic to `core/`
- ❌ Map two different SAP technologies to the same skill file
- ❌ Use `print()` — use `logging`
- ❌ Generate .docx content from within `fsd_generator.py` or `tsd_generator.py`
- ❌ Use inline font formatting (Pt, RGBColor, bold on run) — use named styles
- ❌ Pass raw BRD text to FSD or TSD generation prompts — use structured_summary only
- ❌ Generate all 14 sections in a single API call
- ❌ Create a new Jinja2 `Environment` inside a `core/` module — use `utils/jinja_env.py`
- ❌ Start TSD generation before FSD is complete and downloaded
- ❌ Generate more than one section per LLM call while `INTERACTIVE_GENERATION=true`
- ❌ Advance to the next section before the current one is explicitly locked
- ❌ Ask more than one open question per section — no multi-question batches inside the
  interactive loop
- ❌ Run `interactive_generator.py` and the legacy `split_into_batches` path for the
  same document generation

---

## 9. Testing Expectations

- Every `core/` module has a corresponding test file in `tests/`
- Tests use `pytest` + `unittest.mock` — no real API calls in tests
- `test_brd_summariser.py`: structured dict output, domain detection, missing fields
- `test_brd_parser.py`: PDF, DOCX, multi-file concatenation, malformed file, empty file
- `test_fsd_generator.py`: batch splitting, batch retry, with/without template,
  with/without answers, section content dict assembly
- `test_document_builder.py`: named styles registered, cover page present, TOC field
  present, table header shading, alternating row colours
- `test_interactive_generator.py`: single-section call contract (never >1 section per
  prompt), locked_sections state accumulation across sections, regeneration attempt
  counter and 5-attempt force-lock behaviour, context carry-forward (later sections'
  prompts contain earlier locked content)
- Run all: `pytest tests/ -v`

---

## 10. First-Time Setup

```bash
cd sap_epm_design_agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY and optionally ANTHROPIC_BASE_URL
streamlit run app.py
```

---

## 11. Claude Code Plan Mode Prompt

When entering Plan Mode, use this prompt verbatim:

```
Read CLAUDE.md completely first.
Then read docs/SAP_EPM_Design_Agent_FSD.md.
The FSD is version 2.1. The existing code is version 2.0.
Create a detailed implementation plan for upgrading the codebase from v2.0 to v2.1.
The plan must cover every changed or new file listed in Section 4.4 (FR-10, FR-10a) and
Section 4.5 (FR-15) of the FSD, plus the Interactive Section Loop Contract in CLAUDE.md §3.8a.
Group changes into logical implementation phases.
Do not write any code yet — plan only.
Highlight any ambiguities you find before proceeding.

```
---

*Last updated: July 2026 | Version 2.1 | SAP EPM Design Agent*