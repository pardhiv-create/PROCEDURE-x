# ProcureX — LLM-powered Procurement Agent

Hackathon-ready procurement decision-support MVP built with Streamlit, Python, Pydantic, and the OpenAI Responses API.

## What it demonstrates
- Natural-language purchase requirements with editable structured constraints
- PDF, DOCX, XLSX, CSV, TXT, EML, and Markdown quotation parsing
- Real LLM structured extraction using a Pydantic schema (when `OPENAI_API_KEY` is configured)
- Deterministic mandatory checks: `PASS`, `FAIL`, or `UNKNOWN`
- Anomaly detection for missing terms, suspicious prices, quantity mismatches, and unknown charges
- Recommendation synthesis with a deterministic eligibility safety gate
- Clarification questions and explicit human approval/rejection/request-changes workflow
- JSON audit report and CSV vendor comparison downloads
- Example quotations and automated tests

## Architecture

```
Streamlit UI
   │
   ▼
ProcurementAgent ── OpenAI Responses API (structured Pydantic output)
   │
   ├── Document parser: PDF / DOCX / XLSX / CSV / TXT / EML
   ├── Deterministic validation engine (Python)
   ├── Eligibility gate + cost ranking
   ├── Recommendation / clarification synthesis
   └── Audit and report generation
```

The LLM extracts facts and synthesizes a narrative. Python—not the LLM—calculates compliance status and determines the eligible set. The LLM cannot override failed or unknown mandatory constraints; its recommended vendor is checked against the deterministic eligible list.

## Requirements
- Python 3.10+
- OpenAI API key for live LLM extraction and synthesis
- Internet connection for initial dependency installation and API requests

## Windows setup (VS Code / PowerShell)

1. Extract the ZIP and open the `ProcureX_Hackathon` folder in VS Code.
2. Open Terminal → New Terminal.
3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. Alternatively use Command Prompt: `.venv\Scripts\activate.bat`.

4. Install packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Copy `.env.example` to `.env` and add your API key:

```env
OPENAI_API_KEY=your_real_api_key
OPENAI_MODEL=gpt-4o-mini
ALLOW_DEMO_FALLBACK=true
```

Keep `.env` private. Never commit it or paste the key into a public repository.

6. Run:

```powershell
streamlit run app.py
```

The browser will open the local application. Click **Load sample quotations** to demonstrate the workflow, or upload your own files.

## macOS / Linux setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
streamlit run app.py
```

## Run tests

```bash
pytest -q
```

Tests cover constraint handling, unknown warranty, and exclusion of non-compliant vendors from ranking.

## Demo script (3–5 minutes)
1. Save the laptop requirements in the Requirements tab.
2. Load sample quotations.
3. Run the agent analysis.
4. Show Budget Computing fails RAM and warranty despite being cheaper.
5. Show NextGen Devices requires clarification for missing warranty/delivery.
6. Show Alpha Systems as the compliant candidate among the sample offers.
7. Record a reviewer decision.
8. Download the JSON audit report and CSV comparison.

## Configuration
- `OPENAI_API_KEY`: Required for real API calls. Without it, the system uses transparent fallback extraction and deterministic recommendation.
- `OPENAI_MODEL`: Defaults to `gpt-4o-mini`; set this to a model available to your API account that supports structured outputs.
- `MAX_DOCUMENT_CHARS`: Maximum text passed to the model per document (default 30,000).
- `ALLOW_DEMO_FALLBACK`: `true` enables fallback if the API call fails; use `false` if you want API failures to stop processing visibly.

## Important limitations
- Extraction is only as reliable as the source text and model output. Evidence quotes are model-provided and must be checked against original files.
- Scanned PDFs are not OCR'd in this MVP. Use OCR to make them text-readable first.
- Hardware processor tier is simplified and should be verified against a curated product catalogue for production.
- Tax and fee calculations use extracted values; unknown taxes/fees are flagged, and totals are estimates, not legally binding quotes.
- No emails, purchase orders, payments, or external procurement actions are sent. Approval is a record in the current Streamlit session.
- The audit log is in-memory and resets with the session. Production should use a database, authentication, role-based permissions, durable logs, and data-retention controls.
- Treat vendor files as untrusted input. This MVP asks the model to ignore embedded instructions but is not a substitute for a full prompt-injection/security review.

## Project structure

```
ProcureX_Hackathon/
├── app.py
├── procurex/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── documents.py
│   ├── llm.py
│   ├── reporting.py
│   ├── rules.py
│   └── schemas.py
├── examples/
│   ├── alpha_quote.txt
│   ├── budget_quote.txt
│   └── nextgen_quote.txt
├── tests/
│   └── test_rules.py
├── .env.example
├── .gitignore
├── Dockerfile
└── requirements.txt
```
