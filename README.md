# DREF Assist

**AI-powered assistant for faster IFRC disaster response applications**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Node](https://img.shields.io/badge/Node.js-18%2B-339933?logo=nodedotjs)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61dafb?logo=react)
![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-GPT--4o-ff6f00)
![Built for](https://img.shields.io/badge/Built%20for-IFRC-ED1B2F?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiAyMmgyMEwxMiAyeiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)

DREF Assist helps emergency surveyors complete [DREF (Disaster Response Emergency Fund)](https://www.ifrc.org/disaster-response-emergency-fund-dref) applications faster and to a higher standard. It accepts multimodal inputs — text, PDFs, images, voice recordings, and video — processes them through Azure OpenAI GPT-4o, and automatically populates the DREF application form via a conversational chat interface. When conflicting data is detected across sources, the system pauses for human resolution. A built-in evaluation engine scores the completed application against IFRC rubric criteria and suggests improvements.

---

## Table of Contents

- [Architecture](#architecture)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Tech Stack](#tech-stack)
- [Quickstart](#quickstart)
- [Links](#links)
- [Team](#team)
---

## Architecture

```mermaid
flowchart TB
    subgraph Frontend["prototypefrontend/ — React + TypeScript"]
        UI["DREF Form Wizard<br>(5-step IFRC GO UI)"]
        Chat["AI Chat Assistant<br>(text, files, voice)"]
        Eval["Evaluation Panel<br>(rubric results)"]
    end

    subgraph Backend["backend/ — FastAPI"]
        API["FastAPI Router<br>/api/chat · /api/evaluate"]
        MP["Media Processor<br>PDF · DOCX · Image<br>Audio · Video"]
        LLM["LLM Handler<br>GPT-4o · JSON mode<br>Field extraction"]
        CR["Conflict Resolver<br>Within-batch · Cross-batch<br>Numeric tolerance"]
        DE["DREF Evaluator<br>Pass 1: Rule-based<br>Pass 2: LLM quality"]
    end

    subgraph External["External Services"]
        GPT["Azure OpenAI<br>GPT-4o"]
        Whisper["Azure OpenAI<br>Whisper"]
    end

    UI <--> Chat
    UI <--> Eval
    Chat -- "POST /api/chat<br>(form state + files + history)" --> API
    Eval -- "POST /api/evaluate" --> API
    API --> MP
    MP --> LLM
    LLM --> CR
    API --> DE
    MP -- "audio/video" --> Whisper
    LLM --> GPT
    DE --> GPT
```

> The system is **stateless** — the frontend sends the full form state, conversation history, and files with every request. No database or session storage is required.

---

## Key Features

- **Multimodal input** — upload PDFs, DOCX, images, audio recordings, and video; each processed by a specialised handler
- **Auto field population** — GPT-4o extracts structured data from uploads and chat messages, mapping it to 56 DREF form fields
- **Conflict resolution** — detects contradictions between new data and existing form values, pauses for user decision
- **Automated evaluation** — two-pass scoring (rule-based + LLM) against the IFRC rubric with actionable improvement suggestions
- **IFRC GO integration** — UI styled to match the existing IFRC GO platform to avoid retraining field officers
- **Conversational interface** — natural-language chat with full conversation history for iterative form completion
- **Multilingual support** — GPT-4o handles input in any language; Whisper transcribes non-English audio

---

## Repository Structure

```
DREF-Assist/
├── README.md                  ← You are here
├── backend/                   ← FastAPI backend — AI pipeline, evaluation, API
│   ├── app.py                    Entry point & route definitions
│   ├── services/                 Orchestrator (media → LLM → conflicts)
│   ├── llm_handler/              GPT-4o prompt building, calling, parsing
│   ├── media-processor/          Handlers for PDF, DOCX, image, audio, video
│   ├── conflict_resolver/        Conflict detection & resolution logic
│   ├── dref_evaluation/          Rubric-based evaluation engine (43 criteria)
│   ├── tests/                    End-to-end tests
│   └── README.md                 Detailed backend docs
├── prototypefrontend/         ← React frontend — DREF form UI + chat + evaluation
│   └── drefprototype/
│       ├── src/
│       │   ├── pages/            Multi-step form wizard
│       │   ├── components/       Chat, evaluation panel, form steps, IFRC header/footer
│       │   └── lib/              API client, type definitions, utilities
│       └── README.md             Detailed frontend docs
└── docs/                      ← Design documents & plans
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend framework | FastAPI (Python 3.10+), Uvicorn |
| LLM | Azure OpenAI GPT-4o (JSON mode, temperature 0.1) |
| Speech-to-text | Azure OpenAI Whisper |
| Media processing | PyMuPDF (PDF), python-docx (DOCX), OpenCV (video frames), Pillow, imagehash |
| Frontend framework | React 18 + TypeScript, Vite 7 |
| UI components | shadcn/ui (45+ Radix primitives), Tailwind CSS 3.4 |
| Forms | React Hook Form + Zod validation |
| Server state | TanStack React Query |
| State architecture | Stateless — enriched form state (value + source + timestamp) sent per request |

---

## Quickstart

### Prerequisites

- **Python 3.10+** and **pip**
- **Node.js 18+** and **npm**
- **FFmpeg** (for video frame extraction) — `brew install ffmpeg` / `apt install ffmpeg`
- **Azure OpenAI** resource with GPT-4o and Whisper deployments ([setup guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource))

### 1. Clone

```bash
git clone https://github.com/fbs617/DREF-Assist.git
cd DREF-Assist
```

### 2. Start the backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Create .env with your Azure OpenAI keys (see backend/README.md for all variables)
uvicorn app:app --reload --port 8000
```

> See [backend/README.md](backend/README.md) for the full environment variable table and detailed setup.

### 3. Start the frontend

```bash
cd prototypefrontend/drefprototype
npm install
npm run dev
```

Open **http://localhost:8080** — you should see the IFRC GO-styled DREF form with the AI chat assistant in the bottom-right corner.

> See [prototypefrontend/README.md](prototypefrontend/README.md) for detailed frontend configuration.

---

## Links

| Resource | URL |
|---|---|
| Backend documentation | [backend/README.md](backend/README.md) |
| Frontend documentation | [prototypefrontend/README.md](prototypefrontend/README.md) |
| UCL IXN Programme | [ucl.ac.uk/computer-science/collaborate/ucl-industry-exchange-network-ucl-ixn](https://www.ucl.ac.uk/computer-science/collaborate/ucl-industry-exchange-network-ucl-ixn/) |
| IFRC DREF Information | [ifrc.org/disaster-response-emergency-fund-dref](https://www.ifrc.org/disaster-response-emergency-fund-dref) |
| IFRC GO Platform | [go.ifrc.org](https://go.ifrc.org/) |

---

## Team

**DREF Assist** is a UCL COMP0016 IXN project (2025–26) built for the [International Federation of Red Cross and Red Crescent Societies (IFRC)](https://www.ifrc.org/).

| Name | GitHub |
|---|---|
| Fahad Al Saud | [@fbs617](https://github.com/fbs617) |
| Brendan Loo | [@brendanlhm](https://github.com/brendanlhm) |
| Sameer Chowdhury | [@1sameerchowdhury](https://github.com/1sameerchowdhury) |
| Mohammed Talab | [@MohiCodeHub](https://github.com/MohiCodeHub) |
| Emir Akdag | [@emirakdag0](https://github.com/emirakdag0) |

**Client:** IFRC — International Federation of Red Cross and Red Crescent Societies
**Academic context:** UCL Department of Computer Science — COMP0016 Systems Engineering (IXN), 2025–26

