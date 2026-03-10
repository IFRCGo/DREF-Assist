# DREF Assist — Frontend

![React](https://img.shields.io/badge/React-18.3-61dafb?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178c6?logo=typescript)
![Vite](https://img.shields.io/badge/Vite-7.3-646cff?logo=vite)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06b6d4?logo=tailwindcss)
![License](https://img.shields.io/badge/License-TBD-lightgrey)

The DREF Assist frontend is a **React + TypeScript** application that replicates the IFRC GO DREF application form as a multi-step wizard. It integrates an AI-powered chat assistant (backed by the DREF Assist backend) that accepts text, files, and voice input to auto-populate form fields. The application includes real-time evaluation against IFRC rubric criteria, conflict resolution when contradictory data is detected, and a review-and-submit workflow. The UI is themed to match the existing IFRC GO platform so field officers do not need retraining.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Team and Acknowledgements](#team-and-acknowledgements)
- [License](#license)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│               React Application                 │
│                                                 │
│  ┌───────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Step Form │  │ DREF Assist  │  │Evaluation│ │
│  │  Wizard   │  │    Chat      │  │  Panel   │ │
│  │ (5 steps) │  │ (AI + files) │  │ (rubric) │ │
│  └─────┬─────┘  └──────┬───────┘  └────┬─────┘ │
│        │               │               │       │
│        └───────┬───────┴───────┬───────┘       │
│                │               │                │
│         EnrichedFormState   API Client          │
│         (source + timestamp)  (lib/api.ts)      │
│                                │                │
└────────────────────────────────┼────────────────┘
                                 │  Vite dev proxy
                                 │  /api/* → :8000
                                 ▼
                    ┌────────────────────────┐
                    │   Backend (FastAPI)     │
                    │   localhost:8000        │
                    └────────────────────────┘
```

### Data flow

1. **User fills form** → `handleFieldChange` updates `EnrichedFormState` (value + source + timestamp).
2. **User sends chat message** (optionally with files/audio) → `sendChatMessage()` POSTs to `/api/chat` with current form state and conversation history.
3. **Backend returns** `field_updates` and `conflicts` → Chat displays suggested updates with accept/reject buttons.
4. **User accepts updates** → Form state updates propagate to the active step form.
5. **User clicks "Evaluate"** → `evaluateDref()` or `evaluateSection()` calls the backend → `EvaluationPanel` displays per-criterion pass/fail results with "Improve with AI" buttons that pre-fill the chat.

### Key technologies

| Layer | Technology |
|---|---|
| Framework | React 18 with TypeScript |
| Build tool | Vite 7 (SWC plugin) |
| Styling | Tailwind CSS 3.4 + shadcn/ui (45+ Radix-based components) |
| Forms | React Hook Form + Zod schema validation |
| Server state | TanStack React Query |
| Routing | React Router v6 |
| Testing | Vitest + React Testing Library |

---

## Prerequisites

| Dependency | Version | Notes |
|---|---|---|
| **Node.js** | 18+ | LTS recommended. [Download →](https://nodejs.org/) |
| **npm** | 9+ | Bundled with Node.js. Alternatively, use [Bun](https://bun.sh/) (a `bun.lockb` is present). |
| **DREF Assist backend** | Running | The frontend proxies `/api/*` to `http://127.0.0.1:8000`. See the [backend README](../backend/README.md). |

---

## Environment Variables

The frontend does **not** use a `.env` file. Configuration is handled in [vite.config.ts](drefprototype/vite.config.ts):

| Setting | Current Value | Where to change |
|---|---|---|
| Dev server port | `8080` | `vite.config.ts` → `server.port` |
| Dev server host | `::` (all interfaces) | `vite.config.ts` → `server.host` |
| Backend proxy target | `http://127.0.0.1:8000` | `vite.config.ts` → `server.proxy["/api"].target` |

> If your backend runs on a different host or port, update the proxy target in `vite.config.ts`.

---

## Installation

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/fbs617/DREF-Assist.git
cd DREF-Assist/prototypefrontend/drefprototype

# 2. Install dependencies
npm install

# (Alternative: if you use Bun)
# bun install
```

---

## Running the Application

**Make sure the backend is running first** (see [backend README](../backend/README.md)).

```bash
# From prototypefrontend/drefprototype/
npm run dev
```

**Expected output:**

```
  VITE v7.3.x  ready in XXX ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: http://[::]:8080/
  ➜  press h + enter to show help
```

Open **http://localhost:8080** in your browser. You should see the IFRC GO-styled DREF application form with the AI chat assistant available in the bottom-right corner.

### Other scripts

```bash
npm run build        # Production build → dist/
npm run build:dev    # Development build
npm run preview      # Preview production build locally
npm run lint         # Run ESLint
```

---

## Running Tests

The test suite uses **Vitest** with **jsdom** and **React Testing Library**.

```bash
# Run tests once
npm run test

# Run tests in watch mode (re-runs on file changes)
npm run test:watch
```

> ⚠️ **Note:** The test suite currently contains a single placeholder test (`src/test/example.test.ts`). Test files matching `src/**/*.{test,spec}.{ts,tsx}` are automatically discovered.

---

## Project Structure

```
prototypefrontend/
├── package.json                        # Root workspace dependencies
└── drefprototype/                      # Main React application
    ├── package.json                    # App dependencies & scripts
    ├── index.html                      # HTML entry point
    ├── vite.config.ts                  # Vite config (dev server, proxy, plugins)
    ├── vitest.config.ts                # Test runner config (jsdom, setup file)
    ├── tsconfig.json                   # TypeScript config (paths: @/ → ./src/)
    ├── tailwind.config.ts              # Tailwind + IFRC theme colours + custom fonts
    ├── postcss.config.js               # PostCSS (autoprefixer + Tailwind)
    ├── components.json                 # shadcn/ui configuration
    ├── eslint.config.js                # ESLint rules
    │
    ├── public/
    │   ├── go-logo-2020.svg            # IFRC GO logo
    │   └── ...
    │
    └── src/
        ├── main.tsx                    # React DOM entry point
        ├── App.tsx                     # Root component — React Router + providers
        ├── index.css                   # Global styles, Tailwind directives, IFRC
        │                               #   CSS variables (light + dark mode)
        │
        ├── pages/
        │   ├── Index.tsx               # Main page — 7-step form wizard with chat
        │   │                           #   + evaluation + state management
        │   └── NotFound.tsx            # 404 page
        │
        ├── components/
        │   ├── IFRCHeader.tsx          # IFRC GO-branded top navigation bar
        │   ├── IFRCFooter.tsx          # IFRC footer with links and contact info
        │   ├── StepIndicator.tsx       # Visual 5-step progress bar
        │   │
        │   │  ── Form steps ──
        │   ├── EssentialInformationForm.tsx   # Step 0: Operation overview
        │   ├── EventDetailForm.tsx            # Step 1: Event description + population
        │   ├── ActionsNeedsForm.tsx           # Step 2: NS/IFRC/ICRC actions + gaps
        │   ├── OperationForm.tsx              # Step 3: Targeting, risk, budget, support
        │   ├── TimeframesContactsForm.tsx     # Step 4: Dates + 10 contact fields
        │   ├── ReviewSubmitPage.tsx            # Step 5: Read-only review before submit
        │   │
        │   │  ── AI & Evaluation ──
        │   ├── DREFAssistChat.tsx      # AI chat panel — file upload, audio recording,
        │   │                           #   markdown rendering, accept/reject field
        │   │                           #   updates, conflict resolution UI (~1100 lines)
        │   ├── EvaluationPanel.tsx     # Slide-in panel — per-section rubric results
        │   │                           #   with "Improve with AI" buttons
        │   ├── FinalEvaluationDialog.tsx  # Modal — overall pass/fail summary + progress
        │   │
        │   │  ── Shared ──
        │   ├── FormField.tsx           # Two-column form field layout wrapper
        │   ├── ImageUploadButton.tsx   # Reusable multi-file upload with previews
        │   ├── SharingSection.tsx      # Form sharing/collaboration placeholder
        │   ├── NavLink.tsx             # React Router NavLink wrapper
        │   │
        │   └── ui/                     # 45+ shadcn/ui components (Radix-based)
        │       ├── button.tsx
        │       ├── dialog.tsx
        │       ├── select.tsx
        │       ├── sheet.tsx
        │       ├── toast.tsx
        │       └── ...
        │
        ├── lib/
        │   ├── api.ts                  # Backend API client — sendChatMessage(),
        │   │                           #   evaluateDref(), evaluateSection() + all
        │   │                           #   TypeScript interfaces for API types
        │   ├── fieldLabels.ts          # Field ID → human-readable label mapping
        │   └── utils.ts               # cn() utility for Tailwind class merging
        │
        ├── hooks/
        │   ├── use-mobile.tsx          # Mobile breakpoint detection hook
        │   └── use-toast.ts           # Toast notification hook
        │
        └── test/
            ├── setup.ts               # Vitest setup (Testing Library matchers)
            └── example.test.ts        # Placeholder test
```

### IFRC theming

The UI is styled to match the **IFRC GO platform**:

- **Fonts:** Montserrat (headings), Open Sans (body) — loaded via Google Fonts
- **Colours:** IFRC Red (`--ifrc-red`), IFRC Orange (`--ifrc-orange`), IFRC Dark (`--ifrc-dark`), plus grey variants
- **Dark mode:** Supported via Tailwind's `class` strategy
- **Component library:** [shadcn/ui](https://ui.shadcn.com/) with Slate base colour, configured in `components.json`

---

## Contributing

### Branch naming

```
feature/<short-description>    # New features
fix/<short-description>        # Bug fixes
refactor/<short-description>   # Code restructuring
```

### Opening a pull request

1. Create a feature branch from `main`.
2. Make your changes with clear, atomic commits.
3. Ensure linting passes (`npm run lint`).
4. Run the test suite (`npm run test`).
5. Open a PR against `main` with a description of what changed and why.
6. Request a review from at least one team member.

### Code style

- **TypeScript** for all source files (`.tsx` / `.ts`).
- **Tailwind CSS** utility classes — avoid custom CSS where possible.
- **Path aliases:** Use `@/` imports (e.g. `import { Button } from "@/components/ui/button"`).
- **shadcn/ui:** Add new UI primitives via `npx shadcn-ui@latest add <component>`.

---

## Team and Acknowledgements

**DREF Assist** is a UCL COMP0016 IXN project (2025–26) built for the [International Federation of Red Cross and Red Crescent Societies (IFRC)](https://www.ifrc.org/).

### Team

| Name | GitHub |
|---|---|
| Fahad Al Saud | [@fbs617](https://github.com/fbs617) |
| Brendan Loo | [@brendanlhm](https://github.com/brendanlhm) |
| Sameer Chowdhury | [@1sameerchowdhury](https://github.com/1sameerchowdhury) |
| Mohammed Talab | [@MohiCodeHub](https://github.com/MohiCodeHub) |
| Emir Akdag | [@emirakdag0](https://github.com/emirakdag0) |

### Client

**IFRC** — International Federation of Red Cross and Red Crescent Societies

### Academic context

**UCL** Department of Computer Science — COMP0016 Systems Engineering (IXN), 2025–26

