# SAP EPM Design Agent — Functional Specification Document
**Version:** 2.1 (Updated)
**Date:** July 2026
**Prepared By:** Deepesh Khanna, Capgemini I&D – SAP Portfolio
**Audience:** Solution Architects, Functional Consultants, AI/Dev Team Leads
**Classification:** Internal – Confidential
**Status:** Draft

---

## Change History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0 | June 2025 | Deepesh Khanna | Initial draft |
| 2.0 | July 2025 | Deepesh Khanna | Added multi-document input, discussion notes, two-phase FSD→TSD workflow, project metadata, section-level regeneration, BRD pre-summarisation, domain auto-detection, Word document quality standards |
| 2.1 | July 2026 | Deepesh Khanna | Replaced one-shot clarification Q&A + batched blind generation with an interactive, section-by-section generate → review → refine → lock loop for both FSD and TSD |

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Purpose and Scope](#2-purpose-and-scope)
3. [Stakeholders and User Personas](#3-stakeholders-and-user-personas)
4. [Functional Requirements](#4-functional-requirements)
5. [Agent Knowledge Domains](#5-agent-knowledge-domains)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [User Workflow End-to-End](#7-user-workflow-end-to-end)
8. [Output Document Standards](#8-output-document-standards)
9. [Design Constraints and Principles](#9-design-constraints-and-principles)
10. [Open Items and Future Considerations](#10-open-items-and-future-considerations)
11. [Assumptions and Dependencies](#11-assumptions-and-dependencies)
12. [Application Architecture and Development Standards](#12-application-architecture-and-development-standards)
13. [Glossary](#13-glossary)

---

## 1. Executive Summary

The SAP EPM Design Agent is an AI-powered, Streamlit-based web application that reads a
Business Requirements Document (BRD) and supporting client input, then generates two
professional specification documents in sequence: a Functional Specification Document (FSD)
followed by a Technical Specification Document (TSD). Both outputs are formatted as
downloadable Microsoft Word documents (.docx).

The agent follows a **two-phase generation workflow**. Phase 1 generates the FSD from all
client input (BRD, supporting documents, and discussion notes). The consultant reviews and
downloads the FSD. Phase 2 uses the full FSD content — either held in session or re-uploaded
by the user — as the primary input to generate the TSD. This sequential approach ensures the
TSD is always grounded in the approved functional design, not just a BRD summary.

The agent carries deep embedded domain knowledge spanning SAP BW, SAP BPC, SAP Analytics
Cloud (SAC), SAP Business Data Cloud (BDC), SAP Group Reporting, SAP PaPM, SAP Embedded
Analytics, and the entire CFO-office planning and consolidation spectrum. A key design
principle is output readability: every section follows a structure designed for professional
consulting deliverables, not AI-generated prose dumps.

---

## 2. Purpose and Scope

### 2.1 Purpose
This document defines the complete functional requirements for the SAP EPM Design Agent
version 2.0. It describes what the system must do — not how it is technically implemented.

### 2.2 In Scope
- Ingestion of BRD in PDF or MS Word (.docx) format (mandatory)
- Ingestion of multiple additional supporting documents in PDF or .docx format (optional)
- Free-text discussion notes / client commentary as supplementary input (optional)
- Project metadata input: consultant name, client name, project name (optional)
- User selection of target SAP technology (single selection per session)
- AI-powered BRD pre-summarisation into a structured requirements dict before generation
- Automatic detection of relevant functional domain(s) from BRD content
- AI-powered clarification question flow before document generation
- **Phase 1:** Generation of Functional Specification Document (FSD) as a .docx file
- **Phase 2:** Generation of Technical Specification Document (TSD) using full FSD as input
- Option to use in-session FSD or re-upload a revised FSD for TSD generation
- Support for user-supplied FSD/TSD blank Word templates (optional)
- Section-level regeneration: ability to regenerate a single FSD or TSD section
- Download of both generated documents from the Streamlit UI
- Interactive, per-section generation with an inline confirm/correct loop before each
  section is locked — replaces the prior model of answering all clarification questions
  up front, then generating the full document blind

### 2.3 Out of Scope
- Multi-technology output from a single BRD session
- Test script generation (Phase 3)
- Direct integration with SAP systems (SAC REST API, BW RFC)
- User authentication and multi-tenancy
- Persistent storage beyond the active browser session
- Batch / bulk BRD processing

---

## 3. Stakeholders and User Personas

| Persona | Role | Primary Use of the Agent |
|---|---|---|
| SAP Functional Consultant | Primary User | Converts client BRD + discussion notes into a structured FSD without starting from scratch |
| SAP Technical Consultant / Developer | Primary User | Uses the TSD — generated from the full FSD — to build the solution without further briefing |
| Solution Architect | Secondary User | Reviews AI-generated solution architecture in FSD; optionally revises FSD before TSD generation |
| Presales / Bid Manager | Secondary User | Rapidly generates draft specification artefacts for RFP responses |
| Delivery Manager / Project Lead | Reviewer | Uses documents as baseline for scope, effort, and test planning |

---

## 4. Functional Requirements

### 4.1 Input Collection — Phase 1

#### FR-01 BRD Upload (Mandatory)
- The application shall present a file upload widget accepting PDF (.pdf) and Word (.docx)
  files for the primary BRD document
- Maximum file size per file: 50 MB
- On successful upload: display filename, file size, and page/word count
- On failure: display a clear inline error and block progression

#### FR-02 Supporting Documents Upload (Optional)
- Below the BRD upload, the application shall present a **multi-file upload widget** that
  accepts multiple PDF or .docx files simultaneously
- Label: "Supporting Documents (optional) — meeting minutes, data dictionaries, process
  flows, existing reports, client emails"
- The user may select multiple files at once in a single upload action
- Each uploaded file shall be listed with its filename and size
- All supporting documents shall be extracted and concatenated with the BRD text, clearly
  delimited with a document boundary marker (e.g. `=== DOCUMENT: filename ===`) before
  being passed to the agent
- If no supporting documents are uploaded, the workflow proceeds without them

#### FR-03 Discussion Notes / Client Commentary (Optional)
- Below the supporting documents upload, the application shall present a multi-line
  free-text input area
- Label: "Discussion Notes / Client Commentary (optional)"
- Placeholder text: "Paste notes from client workshops, verbal clarifications, email
  threads, or any additional context not captured in the BRD..."
- Character limit: 5,000 characters (with live counter shown)
- This text is passed to the agent as a clearly labelled input section:
  `=== CLIENT DISCUSSION NOTES ===`
- If left blank, the workflow proceeds without it

#### FR-04 Project Metadata (Optional)
- The application shall present four optional text input fields on the input screen:
  - Consultant Name (pre-fills the "Author" field in document control tables)
  - Client / Account Name (used in document headers and title page)
  - Project Name (used in document title and cover page)
  - Engagement Code (reference number for document control)
- If left blank, defaults are used: Author = "SAP EPM Design Agent", Client = "Client",
  Project = "SAP EPM Implementation"
- These values are stored in session state and injected into every generated document

#### FR-05 Target SAP Technology Selection
- Before BRD analysis begins, the user selects exactly one target SAP technology from a
  dropdown list
- The selection informs all downstream analysis, architecture, and specification content
- Supported options (minimum):
  - SAP Analytics Cloud – Analytics
  - SAP Analytics Cloud – Planning (FP&A)
  - SAP BW/4HANA
  - SAP BW on HANA (7.5)
  - SAP BPC (Standard or Embedded)
  - SAP Group Reporting
  - SAP PaPM (Profitability & Performance Management)
  - SAP Business Data Cloud (BDC)
  - SAP Embedded Analytics (CDS / Fiori)
  - SAP ABAP Custom Development

#### FR-06 Optional Document Templates
- Two optional upload fields: one for FSD template (.docx), one for TSD template (.docx)
- If provided, the template's heading structure is used as the section skeleton
- If not provided, default section schemas are used
- UI must clearly communicate that templates are optional

### 4.2 BRD Pre-Summarisation

#### FR-07 Structured BRD Summary Generation
- Before generating clarification questions or any specification document, the agent shall
  perform a **pre-summarisation pass** on all input content (BRD + supporting docs +
  discussion notes)
- This pass produces a structured internal summary dict containing:
  - `requirements`: list of discrete requirements extracted from input
  - `kpis`: list of KPIs and metrics mentioned or implied
  - `data_sources`: list of source systems, data objects, and integration points identified
  - `domain`: detected primary functional domain(s) (e.g. ["finance", "sales"])
  - `key_entities`: business entities in scope (legal entities, cost centres, products, etc.)
  - `open_gaps`: items that appear incomplete or contradictory in the input
- This structured summary dict — NOT the full raw BRD text — is passed to all subsequent
  LLM calls (clarification questions, FSD generation, TSD generation)
- The raw BRD text is used only in this pre-summarisation step
- This approach reduces token consumption on all downstream calls and improves consistency

#### FR-08 Domain Auto-Detection
- From the structured summary dict, the agent shall identify which functional domain skills
  are relevant (finance, sales, procurement, operations, HR)
- Only relevant domain skills are loaded and injected into subsequent prompts
- If domain cannot be determined, all domain skills are loaded as fallback

### 4.3 Section-Level Interactive Review

#### FR-09 Per-Section Targeted Question
- Clarification is no longer a single up-front batch of questions. Instead, while
  generating a given section, the agent may surface **at most one** open question
  specific to that section's content — never a batch of questions, never asked before
  any content exists
- The question must be answerable by looking at the draft just shown (e.g. "should
  currency translation use a fixed monthly rate or a real-time feed?"), not a generic
  discovery question
- If the agent has no open question for a section (draft is unambiguous given the
  input), no question is shown — the user only confirms or corrects the content
- This is distinct from the deeper BRD-level grilling mechanism used elsewhere in the
  Presales Agent; it is a lighter, single-question confirmation scoped to one section
- Items left unresolved after the maximum regeneration attempts (FR-10) are documented
  in the FSD Assumptions Register or Open Questions Register as appropriate

### 4.4 Phase 1 — FSD Generation

#### FR-10 Section Generation and Review Loop
- Sections are generated **one at a time**, in the order defined by the active section
  structure (uploaded template if provided, otherwise the 14-section default)
- For each section, the system shall:
  1. Generate a draft of that section only, using: the structured BRD summary, relevant
     SAP/domain skills, clarification answers, **plus the locked content and answers of
     every previously approved section**
  2. Display the generated draft in the right-hand panel, with any open question (FR-09)
  3. Present a single free-text input: "Does this look right?" — blank means approved as-is
  4. If the user enters a correction, regenerate the same section incorporating that
     feedback, and return to step 2 (the loop does not advance until the user is
     satisfied)
  5. Once approved (blank response, or an explicit "looks good"), lock the section:
     store its final content and any Q&A exchange, mark it complete in the section
     tracker, and move to the next section
- **Maximum regeneration attempts per section: 5.** If exceeded, the section is
  force-locked using the latest draft, and a note is added to the Open Questions
  Register (Section 4.4, FR-11 sections table item 12) flagging it as "locked after
  maximum revisions — recommend manual review"
- The left-hand step navigator shows every section's status at all times: locked (with
  revision count), current, or pending
- Once the final section is locked, the document is assembled and the download button
  is shown — same as today

#### FR-10a Generation Mode — Architecture Note
- Because each section's generation depends on the previous section's *locked* content
  and answers, this loop requires **exactly one section generated per API call**
- This supersedes the previous multi-section batching approach (grouping sections into
  one call for efficiency) — that approach is incompatible with sequential
  context carry-forward and is retained in the codebase only as an optional legacy
  fallback (see CLAUDE.md §3.7), never active at the same time as the interactive loop
- This trades away some token/latency efficiency in exchange for per-section user
  confidence: expect up to 14+ LLM calls per FSD (more with revisions), versus roughly
  5 batched calls previously

#### FR-11 FSD Mandatory Sections
The FSD shall be written from the perspective of a senior SAP Functional Consultant.
It shall not contain raw code, technical configurations, or developer-level detail.

| Section # | Section Name | Description |
|---|---|---|
| 1 | Document Control | Version, author (from metadata), client, project, approvers, change history table |
| 2 | Executive Summary | Business context, project goals, and scope in plain language |
| 3 | Business Requirements Summary | Structured table of all requirements — sourced from pre-summarisation dict |
| 4 | Functional Domain Context | Domain-specific background and relevant KPIs |
| 5 | Solution Architecture | ASCII/Unicode architecture diagram + narrative. Mandatory — never omit |
| 6 | Functional Design – Reporting / Analytics | Report catalogue table: name, type, users, source, frequency, measures, dimensions |
| 7 | Functional Design – Planning (if applicable) | Planning model: versions, horizon, cycle, drivers, allocations, workflow |
| 8 | Data Requirements | Data entities, source mappings, master data, hierarchies, governance |
| 9 | User Roles and Authorisation Concept | Functional role matrix |
| 10 | Integration Requirements | Integration touchpoints, transformation rules, frequency |
| 11 | Assumptions Register | All assumptions where BRD was silent or questions were skipped |
| 12 | Open Questions Register | Unresolved items needing client clarification |
| 13 | Functional Acceptance Criteria | Testable acceptance criteria per requirement |
| 14 | Glossary | All SAP acronyms and domain terms used in the document |

#### FR-12 FSD Section Regeneration
- After FSD is displayed, the user may select any individual section from a dropdown
  and click "Regenerate Section"
- The agent regenerates only that section, using the same structured summary and context
- The regenerated content replaces the existing section in the assembled document
- The user can re-download the updated document

#### FR-13 FSD Download
- After FSD generation (and any section regeneration), a "Download FSD (.docx)" button
  is prominently displayed
- The FSD is retained in session state for use in Phase 2

### 4.5 Phase 2 — TSD Generation

#### FR-14 FSD Input for TSD — Dual Option
- After FSD download, Phase 2 begins
- The application presents two options for FSD input:
  - **Option A — Use session FSD:** A button "Use generated FSD" that takes the in-session
    FSD bytes directly. The FSD filename and word count are displayed for confirmation.
  - **Option B — Re-upload FSD:** A file upload widget accepting .docx files, allowing the
    user to upload a revised/annotated version of the FSD
- Both options feed the same TSD generation pipeline
- The full parsed FSD text — not a summary — is used as input to TSD generation
- UI clearly explains: "The TSD will be generated from the full content of the FSD above.
  If you revised the FSD locally, upload your revised version before proceeding."

#### FR-15 TSD Generation
- TSD is generated using: full FSD text + structured BRD summary + clarification answers
  + SAP skill + domain skills
- TSD follows the same interactive, section-by-section generate → review → refine →
  lock loop described in FR-10, generating **exactly one section per API call**, with
  each new section's prompt including the full FSD text plus every previously locked
  TSD section's content and answers
- The same per-section targeted question model (FR-09) and 5-attempt regeneration cap
  (FR-10) apply
- The left-hand step navigator shows TSD section status (locked / current / pending)
  the same way it does for FSD generation

#### FR-16 TSD Mandatory Sections
The TSD shall be written for an SAP Technical Consultant or Developer.

| Section # | Section Name | Description |
|---|---|---|
| 1 | Document Control | Version, author (from metadata), client, project, approvers, revision history |
| 2 | Technical Architecture Overview | Component diagram, deployment model, technology stack, system landscape |
| 3 | Data Modelling | InfoObject/dimension design, fact/dimension tables, entity relationships |
| 4 | ETL / Data Flow Design | Source-to-target field mapping, transformation logic, delta/full load, error handling |
| 5 | Reporting / Query Objects | Query/story specs: key figures, characteristics, variables, filters, consumers |
| 6 | Planning Model Design (if applicable) | Aggregation levels, planning functions, sequences, data slices, version management |
| 7 | SAP Object Inventory | All objects to be created/modified: name, type, description, status, transport priority |
| 8 | ABAP / Custom Development Requirements | Custom objects: name, type, purpose, complexity. State explicitly if none required. |
| 9 | Performance Considerations | Partitioning, aggregation, indexing, data volumes, query SLAs — quantified where possible |
| 10 | Security and Authorisation – Technical | Auth objects, field values, data restrictions, BW auth variables |
| 11 | Interface and Integration – Technical | Protocol, API, field mapping reference, frequency, error handling |
| 12 | Technical Acceptance Criteria | Test scenarios per object: steps, expected result, test type |
| 13 | Naming Conventions | Object naming patterns for all SAP artefact types in scope |
| 14 | Technical Assumptions and Constraints | All technical assumptions — environment, version, performance, data |

#### FR-17 TSD Section Regeneration
- Same capability as FR-12 — user may regenerate any individual TSD section
- Regeneration uses full FSD text + structured summary as context

#### FR-18 TSD Download
- After TSD generation (and any section regeneration), a "Download TSD (.docx)" button
  is prominently displayed

---

## 5. Agent Knowledge Domains

### 5.1 Analytics and Data Architecture
- Data warehouse concepts: star schema, snowflake schema, fact/dimension design, SCDs
- OLTP vs OLAP: design philosophy, query patterns, data granularity
- Operational, management, and statutory/regulatory reporting distinctions
- KPI frameworks: lagging vs leading indicators, drill-through, period-over-period analysis
- Data lake and lakehouse concepts as they relate to SAP BDC and Datasphere

### 5.2 SAP Technology Expertise

#### 5.2.1 SAP BW (All Versions) — Dedicated Skill File
- BW 3.5 / BW 7.0 / BW 7.5 / BW on HANA / BW/4HANA (each version's specific objects)
- InfoObjects, InfoCubes, DSOs (Standard, Write-Optimised, Direct Update), aDSOs,
  CompositeProviders, HANA Calculation Views
- Extraction: LO Cockpit (BW 3.5/7.x), ODP (BW/4HANA), CDS-based extraction
- Reporting: BEx Analyser, Analysis for Office (AFO), BEx Web, SAC on BW
- BW/4HANA migration patterns: Shell Conversion, In-Place, Remote Conversion

#### 5.2.2 SAP Analytics Cloud — Dedicated Skill File
- Live connection vs. import model
- SAC Analytics: stories, pages, charts, geo maps, smart insights
- SAC Planning: planning models, versions, data actions, multi-actions, allocations
- SAC sFIN: account-based / cost-element-based integrated financial planning
- SAC REST API and live connections to BW/4HANA and S/4HANA

#### 5.2.3 SAP BPC — Dedicated Skill File
- BPC 7.5 NW / BPC 10.0 / BPC 10.1 Standard and Embedded
- Application sets, dimensions, models, input schedules, business rules
- Script Logic and FOX formula language
- BPC Embedded on BW-IP; BPC-to-SAC migration object mapping

#### 5.2.4 SAP Group Reporting — Dedicated Skill File
- Legal consolidation: IC elimination, currency translation, minority interest
- Consolidation monitor, data collection tasks, validation rules
- Integration with S/4HANA Universal Journal (ACDOCA)

#### 5.2.5 SAP PaPM — Dedicated Skill File
- Profitability modelling: allocation rules, driver-based costing, activity-based costing
- Calculation flows and environments
- Integration with CO-PA and S/4HANA

#### 5.2.6 SAP BDC / Datasphere — Dedicated Skill File
- Datasphere: spaces, data flows, replication flows, analytic models, business layer
- SAP HANA Cloud integration, Open Connectors

#### 5.2.7 SAP Embedded Analytics and CDS — Dedicated Skill File
- CDS view types: basic, composite, consumption, analytical
- Virtual Data Model (VDM) in S/4HANA
- Fiori analytical apps: KPI tiles, overview pages, analytical list pages

#### 5.2.8 SAP ABAP — Dedicated Skill File
- ABAP OO, enhancements (BAdI, user exits, enhancement spots)
- ABAP CDS, AMDP (ABAP Managed Database Procedures)
- Custom infosources, start/end/expert routines

### 5.3 Functional Domain Knowledge

| Domain | Key KPIs / Topics |
|---|---|
| Finance / CFO Office | P&L, Balance Sheet, Cash Flow; EBITDA, Working Capital, DSO, DPO; Rolling Forecasts, ZBB, Driver-Based Planning; IFRS16, Group Consolidation, IC Elimination, Transfer Pricing |
| FP&A | AOP, Budget vs Actual, Variance Analysis, Scenario Planning (Base/Upside/Downside), LRP |
| Sales & Revenue | Revenue by product/region/channel, Gross Margin, Win Rate, Pipeline Coverage, NRR, CAC |
| Procurement & Supply Chain | Spend Analytics, Supplier Scorecards, PPV, Inventory KPIs, OTIF, Demand Planning |
| HR & Workforce | Headcount, Attrition, Cost per Hire, FTE vs Budget, Payroll reconciliation |
| Manufacturing & Operations | OEE, Yield, Scrap Rate, Capacity Utilisation, Production Order Variance |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | BRD pre-summarisation shall complete within 30 seconds for all input files combined up to 100 MB total |
| NFR-02 | Performance | Each FSD/TSD section batch (3–4 sections) shall complete within 60 seconds. Full document generation shall complete within 5 minutes |
| NFR-03 | Usability | The Streamlit UI guides the user through the workflow with clear step labels, progress indicators, and contextual help text |
| NFR-04 | Usability | All LLM calls must show a spinner with a descriptive label (e.g. "Generating Section 1–3 of 14…") |
| NFR-05 | Output Quality | Generated documents must be immediately usable in a professional consulting engagement without structural reformatting |
| NFR-06 | Output Quality | No generated document shall contain raw JSON, API responses, or system prompts in any section body |
| NFR-07 | Output Quality | Documents must use consistent named Word styles — not inline font overrides — so consultants can apply their firm's template via Change Styles |
| NFR-08 | Reliability | If any API call fails, display a user-friendly error with a retry option for that specific section batch — do not lose already-generated sections |
| NFR-09 | Privacy | BRD and supporting document content shall not be logged or persisted beyond the active browser session |
| NFR-10 | Portability | Application runs in a standard Python 3.11+ environment with dependencies in requirements.txt |
| NFR-11 | Maintainability | Each SAP technology has its own dedicated skill file. Prompts are Jinja2 templates. Neither is hardcoded in Python logic. |

---

## 7. User Workflow End-to-End

### Phase 1 — FSD Generation

| Step | User Action | System Response |
|---|---|---|
| 1 | Opens the Streamlit web application | Landing page: app title, brief description, Phase 1 input panel |
| 2 | Uploads BRD (PDF or DOCX) — mandatory | File validated; filename, size, page/word count displayed |
| 3 | (Optional) Uploads supporting documents — multi-file | Each file listed with filename and size; total count shown |
| 4 | (Optional) Enters discussion notes in free-text area | Character counter updates live; field accepts up to 5,000 characters |
| 5 | (Optional) Enters project metadata: consultant, client, project, engagement code | Values stored; shown as a summary card |
| 6 | Selects target SAP technology from dropdown | Technology description shown as info box |
| 7 | (Optional) Uploads FSD template .docx | Template confirmed; structure will be used as FSD skeleton |
| 8 | Clicks 'Analyse Input' | Spinner: "Pre-summarising all input documents…" → structured summary created; domain(s) auto-detected; section plan built from template or 14-section default |
| 9 | Agent begins generating Section 1 | Right panel shows Section 1 draft + any targeted question; left panel shows Section 1 as "current," all others "pending" |
| 9a | User answers the question and/or types a correction, or leaves it blank | If correction given: section regenerates and re-displays (loop repeats, up to 5 attempts). If blank/approved: section locks, left panel updates to "locked," next section generation begins automatically |
| 9b–9n | Repeat 9a for each remaining section | Progress accumulates in the left panel; each new section's generation uses all previously locked sections' content and answers as context |
| 10 | Final section locked | Document assembled automatically; "Download FSD (.docx)" button displayed |
| 11 | (Optional) Selects a locked section from dropdown and clicks 'Regenerate Section' | Only that section is regenerated outside the main loop; document rebuilt; re-download available |
| 12 | Downloads FSD | Browser file download triggered |

### Phase 2 — TSD Generation

| Step | User Action | System Response |
|---|---|---|
| 13 | Clicks 'Proceed to TSD Generation' | Phase 2 panel expands; two FSD input options shown |
| 14 | Option A: Clicks 'Use Session FSD' OR Option B: Uploads revised FSD .docx | Chosen FSD parsed; word count and filename displayed for confirmation |
| 15 | (Optional) Uploads TSD template .docx | Template confirmed |
| 16 | Agent begins generating TSD Section 1 | Same interactive loop as Phase 1 (Steps 9–9n): draft + question shown, user confirms/corrects, section locks, next section begins |
| 17 | Final TSD section locked | Document assembled automatically; "Download TSD (.docx)" button displayed |
| 18 | (Optional) Selects a locked section and clicks 'Regenerate Section' | Only that section regenerated outside the main loop; re-download available |
| 19 | Downloads TSD | Browser file download triggered |
| 20 | (Optional) Clicks 'Start Over' | All session state cleared; returns to Step 1 |

---

## 8. Output Document Standards

### 8.1 Cover Page Requirements
Every generated document shall have a cover page containing:
- Client / Account Name (large, prominent)
- Project Name
- Document type: "Functional Specification Document" or "Technical Specification Document"
- SAP Technology selected
- Version number and status (e.g. "Version 1.0 — Draft")
- Generated date
- Author / Consultant Name
- Engagement Code (if provided)
- Confidentiality classification: "Confidential — Internal Use Only"

### 8.2 Word Style Requirements
- All documents shall use **named Word paragraph styles** — never inline font overrides
- Required named styles: `EPM Heading 1`, `EPM Heading 2`, `EPM Heading 3`,
  `EPM Body Text`, `EPM Table Header`, `EPM Table Body`, `EPM Code Block`,
  `EPM Bullet`, `EPM Caption`
- Heading 1: Arial 16pt Bold, SAP Blue (#1F497D), 12pt space before
- Heading 2: Arial 13pt Bold, SAP Blue (#1F497D), 8pt space before
- Heading 3: Arial 11pt Bold, Dark Grey (#595959), 6pt space before
- Body Text: Arial 10pt, 6pt space after
- Table Header cells: SAP Blue background (#1F497D), white Arial 10pt Bold
- Alternating table row shading: white / light blue (#D6E4F0)
- Code Block: Courier New 9pt, 0.5 inch left indent, light grey background

### 8.3 Structural Standards
- Document Control table immediately after the cover page
- Table of Contents (Word auto-generated field, not static text) on page 3
- Section numbering: hierarchical decimal (1, 1.1, 1.1.1)
- Page header: Document title + version + client name (right-aligned)
- Page footer: Confidentiality classification (left) + "Page X of Y" (right)
- Every document ends with a Glossary section

### 8.4 Content Quality Standards
- Prose paragraphs: maximum 4–6 sentences. Use lists for 3+ related items
- Tables: always use the `EPM Table Header` style for header rows
- No section shall be unstructured prose only — every section uses tables, lists, or both
- No AI-generic phrasing ("Certainly!", "As an AI...", "It is important to note...")
- Write in third person, present tense for requirements; past tense for analysis summaries
- Every KPI or report mentioned in any input document must appear in FSD Section 6 or 7
- Every assumption where a question was skipped must appear in FSD Section 11
- Section 5 (Solution Architecture) must always contain an ASCII/Unicode block diagram

### 8.5 Section Regeneration Quality
- When a section is regenerated, the quality standards above apply identically
- The regenerated section must be contextually consistent with the rest of the document
  (i.e. it receives the full structured summary + existing section titles as context)

---

## 9. Design Constraints and Principles

### 9.1 Architectural Constraints
- Single-user, session-based Streamlit web app — no backend database in Version 2.0
- AI engine: Anthropic Claude API via the Anthropic Python SDK
- All credentials managed via .env — never hardcoded
- Runs on localhost for Version 2.0; cloud deployment is Phase 3

### 9.2 Technology Stack

| Component | Technology |
|---|---|
| UI Framework | Streamlit (Python) |
| AI Engine | Anthropic Claude API (model configurable via CLAUDE_MODEL env var) |
| BRD / Document Parsing — PDF | PyMuPDF (fitz) |
| BRD / Document Parsing — DOCX | python-docx |
| Document Generation | python-docx (named styles approach) |
| Prompt Management | Jinja2 templates (.j2 files in /prompts) |
| Credential Management | python-dotenv (.env file) |
| Python Version | Python 3.11+ |

### 9.3 Generation Architecture — Section Batching

FSD and TSD generation shall use a **batched section generation pattern**:

```
total_sections = 14
batch_size = 3  # configurable via GENERATION_BATCH_SIZE env var
batches = split sections into groups of batch_size

for each batch:
    call LLM with: structured_summary + technology_context + batch_section_specs
    parse returned section content
    store in section_content_dict[section_number]
    update progress indicator

assemble_document(section_content_dict, section_structure)
```

- Each batch call generates 3–4 sections, allowing 2,000–3,000 tokens per section
- If a batch call fails, retry that batch only — do not restart the entire document
- Already-generated sections are preserved in session state during a retry
- `GENERATION_BATCH_SIZE` defaults to 3; configurable in .env

### 9.4 BRD Pre-Summarisation Architecture

```
Input:  raw_brd_text + concatenated_supporting_docs + discussion_notes
Output: structured_summary dict {requirements, kpis, data_sources,
                                  domain, key_entities, open_gaps}
```
The pre-summarisation step is a dedicated LLM call that runs before any other generation:

- All subsequent LLM calls receive `structured_summary` — NOT raw BRD text
- Raw BRD text is read once and then discarded from active prompt context
- This is the primary token optimisation mechanism

### 9.5 Agent Design Principles
- **Functional consultant mindset (FSD):** Maps business requirements to functional
  solution elements — not code or configuration strings
- **Technical consultant mindset (TSD):** Generated from the full FSD, not a summary —
  a developer must need no further briefing after reading it
- **No hallucination guardrails:** Where input is silent and a question was skipped,
  document an assumption — never invent a requirement
- **FSD → TSD traceability:** Every TSD section references the corresponding FSD section
- **Named styles over inline formatting:** Document quality must survive a consultant
  applying their firm's Word template via "Change Styles"

### 9.6 Jinja2 Prompt Architecture

| Layer | Source | Description |
|---|---|---|
| 1 — Base Identity | prompts/base_system.j2 | Always included. Agent persona, quality rules, what never to do. |
| 2 — Skill Injection | skills/sap/<technology>.py + detected domain skills only | get_knowledge() output injected as Jinja2 variables. Only relevant skills loaded. |
| 3 — Task Prompt | prompts/brd_summarisation.j2 / brd_analysis.j2 / fsd_generation_batch.j2 / tsd_generation_batch.j2 | Task-specific instructions with batch section specs injected dynamically. |

---

## 10. Open Items and Future Considerations

| ID | Item | Priority | Phase |
|---|---|---|---|
| OI-01 | Test Script Generation: auto-generate test scripts from FSD Acceptance Criteria | High | Phase 3 |
| OI-02 | SAP Object Validation: cross-check TSD object names against SAP naming convention libraries | Medium | Phase 3 |
| OI-03 | Cloud Deployment: Azure App Service or Streamlit Community Cloud | Low | Phase 3 |
| OI-04 | Document Version Control: compare new BRD against previous FSD/TSD and generate change-impact delta | Medium | Phase 3 |
| OI-05 | RAG — Past Project Reuse: vector store of past FSD/TSD sections for precedent retrieval | High | Phase 3 |
| OI-06 | Multi-language output: Japanese (JERA), Arabic (Al Tayer) | Low | Phase 4 |
| OI-07 | Prompt caching: implement Anthropic prompt caching for structured_summary across batch calls | Medium | Phase 2.1 |
| OI-08 | Batching vs. interactivity tradeoff (FR-10a): confirm the increase in API call count and latency from single-section generation is acceptable, or consider a "fast mode" toggle that falls back to legacy batching | High | Phase 2.1 |
| OI-09 | Confirm 5-attempt regeneration cap (FR-10) is the right ceiling before force-locking a section, and that the force-lock messaging is clear enough for a consultant to know manual review is needed | Medium | Phase 2.1 |

---

## 11. Assumptions and Dependencies

### 11.1 Assumptions
1. The BRD is a reasonably complete requirements document — not a sales deck
2. The user has a valid Anthropic API key with sufficient quota
3. Supporting documents and discussion notes supplement — they do not replace — the BRD
4. Output documents are reviewed and refined by the consulting team before client delivery
5. Application runs with Python 3.11+ and internet access to the Anthropic API
6. The consultant is responsible for the accuracy of project metadata entered

### 11.2 Dependencies
- Anthropic Claude API availability and response latency
- python-docx for Word document generation (named styles)
- Streamlit framework for the web UI
- PyMuPDF for PDF parsing
- Jinja2 for prompt template rendering

---

## 12. Application Architecture and Development Standards

### 12.1 Canonical Folder Structure

```
sap_epm_design_agent/
│
├── app.py                            # Streamlit entry point — UI only
├── CLAUDE.md                         # Claude Code architectural contract
├── .env                              # Credentials and config (never commit)
├── .env.example                      # Safe-to-commit template
├── requirements.txt
├── README.md
├── docs/
│   └── SAP_EPM_Design_Agent_FSD.md  # This document
│
├── core/
│   ├── __init__.py
│   ├── llm_client.py                 # ONLY file that calls Anthropic SDK
│   ├── brd_parser.py                 # PDF + DOCX text extraction
│   ├── brd_summariser.py             # Pre-summarisation LLM call → structured dict
│   ├── question_engine.py            # Clarification question generation
│   ├── fsd_generator.py              # FSD batch generation orchestration
│   ├── tsd_generator.py              # TSD batch generation orchestration
│   ├── section_regenerator.py        # Single-section regeneration logic
│   └── document_builder.py           # python-docx assembly with named styles
│
├── skills/
│   ├── __init__.py                   # Registry + load_sap_skill() + load_domain_skills()
│   ├── sap/
│   │   ├── __init__.py
│   │   ├── bw4hana.py                # BW/4HANA dedicated skill (separate from SAC)
│   │   ├── bw_on_hana.py             # BW 7.5 on HANA dedicated skill
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
│       └── hr.py                     # HR/Workforce domain skill
│
├── prompts/
│   ├── base_system.j2                # Master system prompt
│   ├── brd_summarisation.j2          # Pre-summarisation prompt
│   ├── brd_analysis.j2               # Clarification questions prompt
│   ├── fsd_generation_batch.j2       # Batch FSD section generation
│   ├── tsd_generation_batch.j2       # Batch TSD section generation
│   └── section_regeneration.j2       # Single section regeneration
│
├── templates/
│   ├── fsd_default_structure.py      # Default FSD 14-section schema
│   └── tsd_default_structure.py      # Default TSD 14-section schema
│
├── utils/
│   ├── __init__.py
│   ├── file_handler.py               # Upload validation, multi-file handling
│   ├── session_state.py              # Session state keys + workflow step constants
│   └── jinja_env.py                  # Shared Jinja2 environment (replaces 3 duplicates)
│
└── tests/
    ├── test_brd_parser.py
    ├── test_brd_summariser.py
    ├── test_question_engine.py
    ├── test_fsd_generator.py
    ├── test_tsd_generator.py
    └── test_document_builder.py
```

### 12.2 Layer Architecture

| Layer | Folder / File | Rule |
|---|---|---|
| UI | app.py | Streamlit only. No LLM calls. No business logic. No python-docx. |
| Orchestration | core/ | Business logic, prompt assembly. No Streamlit imports. No direct SDK calls. |
| AI Gateway | core/llm_client.py | ONLY file importing Anthropic SDK. All calls route here. |
| Knowledge | skills/ | Pure knowledge: get_knowledge() → dict. No LLM calls, no I/O. |
| Prompts | prompts/ | Jinja2 .j2 templates only. Variables injected by core/ modules. |
| Documents | core/document_builder.py | All python-docx logic. Named styles only. No inline font overrides. |
| Config | .env | All credentials, model, batch size, token limits. Never in source. |
| Jinja2 Utility | utils/jinja_env.py | Single shared Jinja2 Environment. Used by all core/ modules. |

### 12.3 Scalability Patterns

#### Adding a New SAP Technology
1. Create `skills/sap/<technology>.py` — implement `get_knowledge() -> dict`
2. Register in `skills/__init__.py` under `SAP_SKILL_REGISTRY`
3. Add to `SAP_TECHNOLOGIES` list in `utils/session_state.py`
4. Zero changes to `core/`, `prompts/`, or `app.py`

#### Adding a New Output Document Type (e.g. Test Script)
1. Create `core/test_script_generator.py` following `fsd_generator.py` pattern
2. Create `prompts/test_script_generation_batch.j2`
3. Add section schema to `templates/test_script_default_structure.py`
4. Add download button to `app.py` in Phase 3 panel

#### Modifying Prompt Behaviour
1. Edit the relevant `.j2` file in `prompts/` — zero Python changes
2. Run `pytest tests/` after changes

### 12.4 Environment Configuration

| Variable | Purpose | Default |
|---|---|---|
| ANTHROPIC_API_KEY | Anthropic API key | (required) |
| ANTHROPIC_BASE_URL | Custom API gateway URL (Capgemini internal) | (optional) |
| CLAUDE_MODEL | Model for all LLM calls | claude-sonnet-4-6 |
| MAX_TOKENS_SUMMARISE | Token budget for pre-summarisation call | 2000 |
| MAX_TOKENS_QUESTIONS | Token budget for clarification questions | 1500 |
| MAX_TOKENS_BATCH | Token budget per section batch call | 4000 |
| GENERATION_BATCH_SIZE | Sections per batch call | 3 |
| MAX_FILE_SIZE_MB | Per-file upload size limit | 50 |
| APP_TITLE | Displayed in Streamlit page title | SAP EPM Design Agent |

---

## 13. Glossary

| Term | Definition |
|---|---|
| AFO | Analysis for Office — SAP's Excel-based reporting tool for BW and SAC |
| AOP | Annual Operating Plan — the formal budget / business plan for a fiscal year |
| BAdI | Business Add-In — SAP's standard enhancement mechanism |
| BDC | SAP Business Data Cloud — converged data and analytics platform (Datasphere + SAC) |
| BEx | Business Explorer — SAP BW's legacy reporting and query design toolset |
| BPC | SAP Business Planning & Consolidation — SAP's EPM planning and consolidation tool |
| BRD | Business Requirements Document — the primary input document |
| CDS | Core Data Services — SAP's data definition language for semantic modelling |
| DTP | Data Transfer Process — BW object that moves data between persistent layers |
| FP&A | Financial Planning & Analysis — CFO-office discipline: budgeting, forecasting, variance |
| FSD | Functional Specification Document — describes what the solution will do functionally |
| IC | Intercompany — transactions between entities within the same corporate group |
| InfoObject | SAP BW master data object (characteristic or key figure) |
| KPI | Key Performance Indicator |
| LRP | Long-Range Plan — multi-year strategic financial plan |
| Named Style | A reusable Word paragraph style (e.g. Heading 1) applied by name, not by inline formatting |
| OLAP | Online Analytical Processing — multi-dimensional analysis (cubes, aggregations) |
| OLTP | Online Transaction Processing — transactional ERP/CRM systems |
| ODP | Operational Data Provisioning — SAP standard extraction from S/4HANA to BW |
| PaPM | SAP Profitability and Performance Management |
| Pre-Summarisation | A dedicated LLM pass that converts raw BRD + supporting docs into a structured dict |
| SAC | SAP Analytics Cloud — SAP's cloud-native analytics and planning platform |
| Section Batching | Generating 3–4 document sections per API call for deeper content per section |
| TSD | Technical Specification Document — describes how the solution will be built technically |
| VDM | Virtual Data Model — SAP's semantic CDS view layer in S/4HANA |
| ZBB | Zero-Based Budgeting — every budget line justified from zero, not prior year |

---

*End of Functional Specification Document — Version 2.0 | July 2025 | SAP EPM Design Agent*