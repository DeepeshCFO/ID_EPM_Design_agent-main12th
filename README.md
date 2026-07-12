# SAP EPM Design Agent

An AI-powered Streamlit application that reads a Business Requirements Document (BRD) and generates professional Functional Specification Documents (FSD) and Technical Specification Documents (TSD) for SAP EPM and Analytics implementations.

## Setup

### 1. Create and activate virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env
```

Edit `.env` and add your `ANTHROPIC_API_KEY`.

### 4. Run the application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Usage

1. **Upload BRD** — Upload your Business Requirements Document (PDF or DOCX, max 50 MB)
2. **Select SAP Technology** — Choose the target SAP technology from the dropdown
3. **Optional templates** — Upload blank FSD/TSD Word templates to use as structural skeletons
4. **Analyse BRD** — The agent parses the BRD and generates clarification questions
5. **Answer questions** — Answer any clarification questions, or skip all
6. **Generate Documents** — Download the generated FSD and TSD as `.docx` files

## Supported SAP Technologies

- SAP Analytics Cloud – Analytics
- SAP Analytics Cloud – Planning (FP&A)
- SAP BW/4HANA
- SAP BW on HANA (7.5)
- SAP BPC (Standard or Embedded)
- SAP Group Reporting
- SAP PaPM
- SAP Business Data Cloud (BDC)
- SAP Embedded Analytics (CDS / Fiori)
- SAP ABAP Custom Development

## Running Tests

```bash
pytest tests/ -v
```

## Architecture

See `CLAUDE.md` for the full architectural contract and layer separation rules.
