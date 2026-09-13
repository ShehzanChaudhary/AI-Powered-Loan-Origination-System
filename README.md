## AI-Powered Loan Origination System (LOS)
**The Problem**

Bank loan underwriting is traditionally a manual process: a loan officer reads through a stack of applicant documents (identity proof, salary slip, bank statement, tax returns, loan application, existing loan history), manually cross-checks details across them for consistency and possible fraud, separately pulls a credit bureau report, and then decides whether to approve or reject the loan. This is slow, inconsistent across officers, and hard to audit.

**The Solution**

An AI-powered Loan Origination System that automates the entire underwriting pipeline end-to-end: it extracts and classifies every applicant document, cross-verifies applicant details across all of them, pulls a credit bureau report, computes a risk score, and reaches a final lending decision — all in a single automated flow behind a secure, role-based web application.

The system is built on one core design rule: credit decisions must be deterministic and rule-based, not AI judgment — so outcomes are consistent, explainable, and auditable, which is a real regulatory requirement in lending. AI (an LLM) is used only for document understanding (classification fallback, field extraction) and for explaining an already-made, rule-based decision in plain language — it never makes the decision itself. Every point in the risk scorecard and every approve/reject/manual-review outcome comes from deterministic code, not a model's judgment.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend language | Python |
| Backend framework | FastAPI (fully async, end-to-end) |
| OCR / Document Extraction | **Azure Document Intelligence** — `prebuilt-layout` model for general text/tables, `prebuilt-idDocument` model for Aadhaar/PAN |
| LLM | **OpenRouter** (OpenAI-compatible API), model `openai/gpt-4o-mini` — used for field extraction, classification fallback, and decision justification |
| Document Classification | Rule-based keyword matching (fast path) + LLM fallback for low-confidence/non-English/unusual-format documents |
| Cross-Document Verification | Rule-based: `rapidfuzz` for fuzzy text matching, `python-dateutil` for date normalization |
| Credit Bureau | Demo/mock CIBIL-style API (own FastAPI endpoint), called via a real HTTP adapter — architected so swapping to a real bureau later only changes the adapter, not the schema or anything downstream |
| Risk Scoring | Rule-based additive scorecard (fully auditable — every point has a human-readable reason) |
| Final Decision | Rule-based: hard-decline rules checked first, then risk-band fallback |
| Database | MySQL, via SQLAlchemy (async, `asyncmy` driver) |
| Auth | JWT-based, role system (`ADMIN` / `LOAN_OFFICER`), admin bootstrapped from `.env` on first startup, new officer accounts created by admin only (no public signup) |
| Frontend | React + TypeScript (Vite), Tailwind CSS v4, React Router |
| Async pattern | `AsyncOpenAI`, Azure's async client, `asyncio.gather()` for parallel document processing, `asyncio.to_thread()` for unavoidable sync calls (e.g. `zipfile`) |

---

## Project Structure

```
app/
 ├── api/routes/
 │    ├── application.py         → POST /api/v1/applications/upload  (the main pipeline)
 │    ├── credit_bureau.py       → GET /api/v1/bureau/credit-report/{pan}  (demo CIBIL endpoint)
 │    └── auth.py                → POST /api/v1/auth/login, POST /api/v1/auth/register (admin-only)
 ├── adapters/                     → ONE client per external service, singleton, with retry/backoff
 │    ├── openrouter.py
 │    ├── document_intelligence.py
 │    ├── credit_bureau.py         → HTTP adapter calling our own demo endpoint
 │    └── logger.py
 ├── core/
 │    ├── config.py                → pydantic-settings, reads .env
 │    ├── database.py              → async SQLAlchemy engine/session
 │    ├── security.py              → password hashing, JWT create/decode
 │    └── deps.py                  → get_current_user, get_current_admin
 ├── models/                       → SQLAlchemy ORM models
 │    ├── loan_application.py
 │    └── user.py
 ├── schemas/                      → Pydantic models, no logic
 │    ├── application.py           → ApplicationResponse + 7 per-document-type field schemas
 │    ├── credit_bureau.py         → CibilReport and nested models
 │    └── auth.py
 ├── services/                     → business logic, uses adapters, never creates its own client
 │    ├── ingestion/zip_handler.py
 │    ├── document/
 │    │    ├── document_classifier.py   → keyword + LLM fallback
 │    │    ├── document_extractor.py
 │    │    └── field_extractor.py       → routes to Azure ID model or LLM, per-type schema
 │    ├── verification/cross_document_verifier.py
 │    ├── risk/risk_scorer.py
 │    ├── decision/
 │    │    ├── decision_engine.py
 │    │    └── justification_generator.py
 │    └── persistence/application_repository.py
 ├── prompts/                      → Jinja2 templates for every LLM call
 │    ├── extract_fields.jinja2
 │    ├── classify_document.jinja2
 │    └── generate_justification.jinja2
 └── main.py                       → FastAPI app, CORS, lifespan (admin bootstrap, table creation, client shutdown)

frontend/src/
 ├── api/          → axios client + typed API calls
 ├── types/         → TypeScript types mirroring backend Pydantic schemas
 ├── context/       → AuthContext, ApplicationContext
 ├── components/    → ProtectedRoute, results/ (DecisionBanner, RiskScorecard, VerificationChecks, DocumentsList, CreditReportSummary)
 └── pages/         → LoginPage, UploadPage, ResultsPage

data/
 ├── uploads/{application_id}/     → raw uploaded ZIP
 └── extracted/{application_id}/   → unzipped documents
```

**Architecture pattern:** `adapters/` = external API clients only. `services/` = business logic. `schemas/`/`models/` = data shapes. `core/` = cross-cutting concerns (config, DB, security).

---

## The Full Pipeline

A single `POST /api/v1/applications/upload` call (protected — requires a JWT) runs all of this:

1. **Ingestion** — ZIP is validated and extracted.
2. **Layout Extraction** — every document sent to Azure Document Intelligence concurrently (`asyncio.gather`).
3. **Classification** — fast keyword match first; if confidence is too low (different language, unusual phrasing/format), falls back to an LLM classifier.
4. **Field Extraction** — each document routed to its own Pydantic schema (Aadhaar, PAN, Salary Slip, Bank Statement, ITR, Loan Application, Loan History) and either Azure's ID model (Aadhaar/PAN) or an LLM call with a dynamically-built, schema-driven prompt.
5. **Cross-Document Verification** — rule-based fuzzy/exact matching of Name, DOB, PAN, Address, Employer, and Salary across documents. Produces `MATCHED` / `MISMATCH` / `MISSING` per field.
6. **Credit Bureau Lookup** — fetches a CIBIL-style report for the applicant's PAN (demo data).
7. **Risk Scoring** — deterministic additive scorecard: Credit Score, FOIR, Verification status, Credit Account Health, Recent Enquiries. Produces a `LOW` / `MEDIUM` / `HIGH` risk band.
8. **Final Decision** — hard-decline rules checked first (identity mismatch → manual review, written-off account → reject, open dispute → manual review), then falls back to the risk band. Produces `APPROVED` / `REJECTED` / `MANUAL_REVIEW`.
9. **LLM Justification** — a plain-language paragraph explaining the already-made decision, generated from the exact facts above (never allowed to change or second-guess the decision).
10. **Persistence** — the full result is saved to MySQL (core fields as real columns, rich nested data as JSON columns).

Every external-service stage (Azure, OpenRouter, credit bureau, database) is wrapped so that **a failure there never crashes the whole request** — it degrades gracefully (null field + logged error) instead.

---

## Document Schemas

Each of the 7 supported document types has its own Pydantic schema (not one generic shared schema), so extraction can capture what's actually meaningful per type:

- `AadhaarFields`, `PanFields` — via Azure's ID model, LLM fallback
- `SalarySlipFields`, `BankStatementFields`, `ItrFields`, `LoanApplicationFields`, `LoanHistoryFields` — via LLM, with a dynamically-generated JSON schema + field descriptions injected into the prompt (so ambiguous field names like `employment_type` don't get misinterpreted by the LLM)

`CREDIT_INFORMATION` and `GROUND_TRUTH_PROFILE` (a testing-only reference file, never expected in a real applicant ZIP) are intentionally left unmapped — they're skipped, not errored.

---

## Authentication

- Role-based: `ADMIN` and `LOAN_OFFICER`.
- On first startup, an admin account is bootstrapped from `.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`) — this is a one-time, idempotent operation.
- `POST /api/v1/auth/login` — any active user gets a JWT.
- `POST /api/v1/auth/register` — **admin-only** (protected by `get_current_admin` dependency), creates new Loan Officer accounts. No public signup.
- `POST /api/v1/applications/upload` — requires a valid JWT (any role).

---

## API Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/login` | none | Get a JWT |
| POST | `/api/v1/auth/register` | Admin only | Create a Loan Officer account |
| POST | `/api/v1/applications/upload` | Any logged-in user | Run the full pipeline on a ZIP |
| GET | `/api/v1/bureau/credit-report/{pan}` | none (demo) | Demo CIBIL-style report |
| GET | `/health` | none | Health check |

---

## Environment Variables (`.env`)

```env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=openai/gpt-4o-mini

CREDIT_BUREAU_BASE_URL=http://127.0.0.1:8000

DATABASE_URL=mysql+asyncmy://<user>:<password>@<host>:<port>/<db_name>

JWT_SECRET_KEY=<random 32+ char secret, e.g. via `openssl rand -hex 32`>
ADMIN_USERNAME=
ADMIN_PASSWORD=
ADMIN_EMAIL=
```

---

## Setup

### Backend
```bash
pip install fastapi uvicorn python-multipart
pip install azure-ai-documentintelligence openai httpx
pip install pydantic pydantic-settings
pip install rapidfuzz python-dateutil
pip install sqlalchemy asyncmy
pip install bcrypt "python-jose[cryptography]"

uvicorn app.main:app --reload
```
On startup: DB tables are created if they don't exist, and the admin account is bootstrapped from `.env`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173` by default; backend CORS is configured to allow this origin.

---

## What's Built (Phase-by-Phase)

- ✅ **Phase 0** — Synthetic test dataset (fictional applicant, watermarked documents)
- ✅ **Phase 1** — Ingestion + Document Extraction (Azure Document Intelligence)
- ✅ **Phase 2** — Classification (keyword + LLM fallback)
- ✅ **Phase 3** — Per-document-type structured Field Extraction
- ✅ **Phase 4** — Cross-Document Verification
- ✅ **Phase 5** — Credit Bureau Integration (demo) + Risk Scoring
- ✅ **Phase 6** — Final Decision Engine + LLM Justification
- ⏸️ **Phase 7** — Orchestration + Activity Log — **skipped for now**
- ✅ **Phase 8** — MySQL Persistence — **built, end-to-end test still pending**
- ✅ **Phase 9** — React + TypeScript Frontend (Login, Upload, Results pages) + role-based Auth

---

## Known Issues / Pending Work

1. **Performance (paused).** Full pipeline can take up to ~1 minute. Root cause confirmed via logs: Azure Document Intelligence's free **F0 tier** rate-limits concurrent requests (`429` errors seen in logs), and `asyncio.gather()` sends all documents at once. Fix not yet implemented — likely an `asyncio.Semaphore` to cap concurrent Azure calls.
2. **Phase 8 (MySQL) not yet fully tested end-to-end** — the code is written and wired in, but a confirmed successful row-in-database test is still pending.
3. **Email Notifications — not built.** Planned: emails on `APPROVED`, `REJECTED`, `MANUAL_REVIEW` (mismatch), and "documents missing" outcomes.
4. **Missing Document Detection — not built.** The system currently only processes whatever documents are present in the uploaded ZIP; it doesn't yet detect or flag if a required document type (e.g. Salary Slip) is missing entirely.
5. **Activity Log (Phase 7) — skipped.** No structured, timestamped audit trail of pipeline stages yet (currently only console logging via `app/adapters/logger.py`).
6. **Results page has no persistence-backed reload.** The frontend `ApplicationContext` holds the result only in memory — refreshing the Results page loses the data (no `GET /applications/{id}` endpoint exists yet to refetch from MySQL).
7. **Frontend `API_BASE_URL` is hardcoded** to `http://127.0.0.1:8000` in `src/api/client.ts` — needs to move to an env var before any real deployment.

---
