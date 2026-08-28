# UI/UX PRD — SIH25104 Language Agnostic Chatbot
## Screen-by-screen element spec, design system, and Stitch → Antigravity build plan

**Companion docs:** `01_Team_Split_and_Roadmap.md`, `02_PRD_Antigravity.md` (this file inherits its API contract from Section 9 there — do not redefine endpoints, only wire to them)

> **Why this doc exists:** Handing a UI-generation tool a vague brief ("clean modern chat app") is exactly what produces the generic look everyone now recognizes as AI-made — the same cream-and-serif hero, the same rounded chat bubbles, the same purple gradient. This doc fixes that two ways: (1) a specific, opinionated design system (Section 2) baked into every Stitch prompt so the output has a point of view instead of defaulting to a template, and (2) an explicit element-by-element inventory (Section 3) so nothing gets left as a Stitch guess. Section 5 gives you paste-ready Stitch prompts; Section 6 is what to tell the Antigravity agent once the design comes back, so every screen is wired to real backend calls, not static mockup data.

---

## 1. How Stitch + Antigravity fits into this build

- **Stitch** generates the actual visual design (multi-screen, consistent flow) from a text prompt and exports a `DESIGN.md` design-token file plus React/Tailwind (or HTML/CSS) for each screen.
- **Antigravity**, via the Stitch MCP connector, pulls that design directly into the workspace — it does not need to "guess" the visual system, it reads `DESIGN.md` and the exported components.
- Your job is to make sure (a) the Stitch prompt is specific enough that the design doesn't default to generic patterns, and (b) once the design lands in the repo, an Antigravity mission explicitly wires every interactive element to the FastAPI backend from `02_PRD_Antigravity.md` — Stitch does not know your backend, so this wiring step must be a separate, explicit instruction (see Section 6).

**Sequence per screen group:**
1. Paste the relevant Stitch prompt (Section 5) into Stitch → generate → review → export (MCP or zip) into `/frontend`.
2. Confirm `DESIGN.md` tokens match Section 2 (if Stitch drifted, regenerate with a tighter prompt rather than accepting a close-enough palette).
3. Dispatch an Antigravity mission (Section 6) to wire the exported screen to the real API contract, replacing any placeholder/mock data.
4. Run the anti-slop checklist (Section 7) before accepting the Artifact.

---

## 2. Design system (feed this into every Stitch prompt verbatim)

### 2.1 Design brief in one sentence
An **official, multilingual public-information counter** — the feeling of a trustworthy government registry desk that happens to be digital: every answer that's grounded gets a visible "stamp" of its source; anything unverified is visibly marked as such, never hidden or dressed up.

### 2.2 Why not the default look
Explicitly avoiding: (a) warm cream background + high-contrast serif + terracotta/clay accent, (b) near-black background + single neon accent, (c) hairline-rule broadsheet layout with zero border-radius. This project's own signature (the verification stamp, Section 2.5) replaces all three.

### 2.3 Color tokens

| Token | Hex | Use |
|---|---|---|
| `ink-indigo` | `#1F2B4D` | Primary text, headers, nav, primary buttons |
| `turmeric-gold` | `#D9A62E` | Primary accent — active states, links, the "verified stamp" ink |
| `mist-paper` | `#EFF1EC` | App background (cool, pale sage-grey paper — not cream) |
| `banyan-green` | `#2F5D50` | Success/approved/indexed states |
| `slate-line` | `#8A8F98` | Hairlines, secondary text, timestamps |
| `alert-rust` | `#B5482E` | Fallback/error/unanswered states, destructive actions |

### 2.4 Typography

| Role | Latin script | Devanagari/Odia script | Notes |
|---|---|---|---|
| Display (headings) | Fraunces (high-contrast serif) | Noto Serif Devanagari / Noto Serif Oriya | Used sparingly — page titles and empty-state headlines only |
| Body | Inter | Noto Sans Devanagari / Noto Sans Oriya | Chat text, forms, all reading content |
| Utility/data | IBM Plex Mono | IBM Plex Mono (numerals/Latin fallback) | Timestamps, page numbers, confidence scores, source stamps, IDs |

Pairing rule: whatever script a message is rendered in, body text uses the matching Noto Sans variant so mixed-language chat threads stay visually consistent rather than falling back to a mismatched system font.

### 2.5 Signature element — "The Verification Stamp"
Every **grounded** bot answer ends with a small stamp-style badge: a thin double-ruled rectangle, `turmeric-gold` border, small-caps `IBM Plex Mono` text reading the document name + page (e.g. `SCHOLARSHIP POLICY · P.12`), rotated **-2°**, as if physically stamped onto the message. Every **fallback** answer instead gets a dashed `alert-rust` outline badge reading `UNVERIFIED — NO SOURCE FOUND`, not rotated, deliberately less "official-looking." This single device carries the project's core trust requirement (FR-09/FR-16) visually, everywhere, without needing extra copy to explain it.

### 2.6 Layout concept
Rectangular message cards, not rounded chat bubbles (rounded bubbles are the generic-chatbot tell). User messages: left border 3px `ink-indigo`, right-aligned. Bot messages: left border 3px `turmeric-gold` (or `alert-rust` if fallback), left-aligned, stamp badge bottom-right of the card. Admin screens use a dense registry-table layout (thin `slate-line` hairlines, monospace numerics) rather than card grids.

### 2.7 Motion
Minimal. One deliberate moment: the stamp badge "lands" with a quick 120ms scale+rotate-in when a grounded answer finishes streaming — this is the one animation the design spends its budget on. No hover-bounce, no gradient shimmer, no page-load choreography elsewhere.

---

## 3. Screen-by-screen element inventory

For each screen: what's on it, where, and its state variants. Backend wiring for every interactive element is in the Section 4 table (cross-referenced by ID, e.g. `[C-01]`).

### 3.1 Auth — Login / Register
- Institution wordmark + tagline (top-left, small, `ink-indigo` on `mist-paper`)
- Language selector for the interface itself (top-right dropdown: English/Hindi/Odia/+) `[C-01]`
- Email + password fields, "Login" primary button `[C-02]`, "Register" link `[C-03]`
- Role is never a field the user picks — assigned server-side
- Error state: inline `alert-rust` text under the field that failed, not a toast

### 3.2 Chat — Main screen (primary user surface)
- **Left rail (collapsible on mobile):** conversation list — each item shows first message snippet + relative timestamp (`IBM Plex Mono`) `[C-04]`; "+ New conversation" button at top `[C-05]`
- **Header bar:** detected-language chip next to the conversation title, updates per message (e.g. `HINDI` pill in `turmeric-gold` outline) `[C-06]`; user menu (top-right) with logout `[C-07]`
- **Message thread (center):**
  - User message card (right-aligned, `ink-indigo` left-border)
  - Bot message card (left-aligned):
    - Answer text in the response language
    - Verification stamp badge (Section 2.5) `[C-08]` — tapping it expands a small panel showing the exact retrieved excerpt
    - Fallback badge variant when `is_fallback: true`
    - Thumbs-up / thumbs-down icons, bottom-left of the card `[C-09]`
  - "Thinking" state: three static dots in `slate-line`, no animated typing-bubble skeuomorph
- **Composer (bottom, sticky):** auto-growing text field with placeholder in the currently-selected interface language; send button disabled until non-empty `[C-10]`; a small persistent hint line under the field: "Ask in any language — English, Hindi, Hinglish, Odia"
- **Empty state (new conversation):** not a mascot illustration — three example queries as tappable chips, each in a different supported language, demonstrating the cross-lingual premise directly `[C-11]`

### 3.3 Admin — Document Library
- Registry-style table: columns `Document`, `Department`, `Language`, `Version`, `Status`, `Uploaded`, `Actions`
- Status column renders as a small labeled tag, not a colored dot: `PENDING` (slate), `VALIDATED` (slate), `APPROVED` (turmeric-gold), `INDEXED` (banyan-green), `SUPERSEDED` (strikethrough, slate) `[C-12]`
- Row actions: `Approve` `[C-13]`, `Supersede` `[C-14]`, `Delete` `[C-15]` (delete requires a confirm step — text input matching the filename, not just a modal button, given these are official documents)
- "Upload document" button, top-right, opens the upload flow `[C-16]`
- Filter bar: department, language, status (all client-side against the loaded list, no separate endpoints needed)

### 3.4 Admin — Upload flow
- Drag-and-drop zone (or click to browse), PDF only for v1, with explicit file-type/size messaging `[C-17]`
- Metadata form shown after file selection: department (dropdown), language (dropdown), version (text) `[C-18]`
- Submit → progress indicator with real pipeline stages named explicitly: `Extracting text → Chunking → Generating embeddings → Awaiting approval` (mirrors the actual ingestion pipeline, not a generic spinner) `[C-19]`
- On completion: redirect to Document Library with the new row highlighted in its `PENDING`/`VALIDATED` state

### 3.5 Admin — Unanswered Queries (fallback review)
- List of queries that triggered `is_fallback: true`, each showing: query text, detected language, timestamp, conversation link
- Per-row action: "Mark as needs new document" `[C-20]` or "Dismiss (out of scope)" `[C-21]`
- Purpose note at top of screen: this list is the primary signal for what documents to add next — framed as an actionable backlog, not just a log

### 3.6 Admin — Analytics dashboard
- Four stat tiles, monospace numerals: Total queries, Successful-retrieval rate, Fallback rate, P95 latency `[C-22]`
- Simple bar chart: queries by language (last 30 days) `[C-23]`
- Simple bar chart: top topics/documents by retrieval frequency `[C-24]`
- No decorative iconography on the tiles — the numbers and their labels carry the design, per the registry-desk concept

### 3.7 Super Admin — Users & Languages
- Admin user table: name, email, role, created date; "Add admin" button `[C-25]`
- Supported-languages list with add/remove `[C-26]` — each entry shows the language name in its own script next to the English name, reinforcing the multilingual premise in the UI itself

### 3.8 Shared system states (apply across all screens)
- **Loading:** static skeleton blocks in `mist-paper`/`slate-line`, no shimmer animation
- **Error (network/server):** inline banner, `alert-rust` left border, plain-language message + retry action — never a raw status code shown to the user
- **Empty states:** always an instruction, never just "No data" (e.g. Document Library empty → "No documents yet — upload your first institutional document to make the chatbot answer from it.")

---

## 4. Component → Backend endpoint mapping

Every interactive element above is wired to the API contract defined in `02_PRD_Antigravity.md` Section 9. This table is the wiring checklist for the Antigravity "connect the UI" missions — nothing here should end up calling mock/local data once wiring is complete.

| ID | Element | Endpoint | Method | Notes |
|---|---|---|---|---|
| C-01 | Interface language selector | — (client-side only) | — | Sets UI locale; does not affect chat detection |
| C-02 | Login button | `/api/v1/auth/login` | POST | On success, store JWT, redirect by role |
| C-03 | Register link/form | `/api/v1/auth/register` | POST | Default role `student` |
| C-04 | Conversation list item | `GET /api/v1/conversations` * | GET | *Not yet in v1 contract — add as `GET /api/v1/conversations` returning `[{id, last_message, updated_at}]`; flag this addition explicitly when implementing |
| C-05 | New conversation | — (client-side) | — | `conversation_id: null` sent on first `/chat` call |
| C-06 | Detected-language chip | from `/api/v1/chat` response | — | Reads `detected_language` field per message |
| C-07 | Logout | — (client-side) | — | Clear JWT, redirect to login |
| C-08 | Verification stamp / excerpt expand | from `/api/v1/chat` response | — | Reads `sources[]`; excerpt panel needs source **chunk text**, not just document+page — flag as a contract addition: `sources[].excerpt` |
| C-09 | Thumbs up/down | `/api/v1/feedback` | POST | `message_id` must be returned by `/chat` — flag as contract addition if not already present |
| C-10 | Send message | `/api/v1/chat` | POST | Primary interaction; disable while awaiting response |
| C-11 | Example query chips | — (client-side, pre-fills composer) | — | No call until user sends |
| C-12 | Status tag | `GET /api/v1/admin/documents` | GET | Reflects `document_metadata.status` |
| C-13 | Approve action | `PATCH /api/v1/admin/documents/{id}` | PATCH | `{status: "approved"}` |
| C-14 | Supersede action | `PATCH /api/v1/admin/documents/{id}` | PATCH | `{status: "superseded"}` + new upload flow for replacement |
| C-15 | Delete action | `DELETE /api/v1/admin/documents/{id}` | DELETE | Confirm-by-typing-filename before call fires |
| C-16 | Upload document button | opens flow | — | — |
| C-17/18 | File + metadata form | `POST /api/v1/admin/documents` | POST (multipart) | Matches Section 7.1 `document_metadata` fields |
| C-19 | Ingestion progress stages | `GET /api/v1/admin/documents/{id}/status` | GET (poll) | Poll every 2–3s until `indexed` or `error` |
| C-20/21 | Fallback query actions | `GET /api/v1/admin/unanswered-queries` * | GET/PATCH | *Add `PATCH` variant to mark reviewed/dismissed — flag as contract addition |
| C-22/23/24 | Analytics tiles/charts | `GET /api/v1/admin/analytics` | GET | Matches `analytics_daily` schema |
| C-25 | Add admin | `POST /api/v1/admin/users` | POST | Super admin only |
| C-26 | Manage languages | `GET/PUT /api/v1/admin/languages` | GET/PUT | Super admin only |

**Contract additions surfaced by this UI pass** (update `02_PRD_Antigravity.md` Section 9 to match before/while building):
1. `GET /api/v1/conversations` — list a user's conversations for the left rail.
2. `sources[].excerpt` field on the `/chat` response — needed for the stamp's expandable excerpt.
3. `message_id` field on the `/chat` response — needed so feedback can reference the exact message.
4. `PATCH /api/v1/admin/unanswered-queries/{id}` — mark a fallback query as reviewed/dismissed.

This is exactly the kind of drift the "Contract fidelity" Rule in `02_PRD_Antigravity.md` Section 13 is meant to catch — treat these four as required contract-file edits, not just UI-side assumptions.

---

## 5. Stitch prompts (paste directly into Stitch)

Each prompt embeds the design tokens from Section 2 so Stitch's output has this project's point of view rather than a default. Generate as **one multi-screen flow** per group so Stitch keeps them visually consistent; do the Chat flow and Admin flow as two separate Stitch projects since their layouts diverge (card-thread vs. registry-table).

### 5.1 Stitch prompt — Auth + Chat flow (student-facing)
```
Design a multi-screen web app called "[Your institution] Information Desk" —
a multilingual chatbot for students to ask questions about official
institutional documents (scholarships, admissions, hostel rules, exams)
in their own language and get sourced, trustworthy answers.

Design direction: "official multilingual public-information counter" —
trustworthy like a government registry desk, not a generic startup chat app.

Color tokens (use exactly): background #EFF1EC (cool pale paper, NOT warm
cream), primary text/header #1F2B4D (ink indigo), primary accent
#D9A62E (turmeric gold), success #2F5D50 (banyan green), secondary text/
hairlines #8A8F98 (slate), error/warning #B5482E (alert rust).

Typography: display headings in a high-contrast serif (Fraunces or similar),
used sparingly — only page titles and empty states. Body text in Inter.
Timestamps, IDs, and data labels in a monospace face (IBM Plex Mono).

Screens to design:
1. Login screen — wordmark top-left, interface language dropdown top-right,
   email/password form, minimal.
2. Chat screen — left rail with collapsible conversation list (snippet +
   monospace relative timestamp), header bar with a language-detected pill
   next to the conversation title, main thread of RECTANGULAR message cards
   (NOT rounded chat bubbles) — user messages right-aligned with a 3px ink-
   indigo left border, bot messages left-aligned with a 3px turmeric-gold
   left border. Every bot answer ends with a small stamped badge: a thin
   double-ruled rectangle, turmeric-gold border, small-caps monospace text
   like "SCHOLARSHIP POLICY · P.12", rotated -2 degrees, styled like a
   physical document stamp. Include a variant of this badge in dashed
   alert-rust reading "UNVERIFIED — NO SOURCE FOUND" for answers with no
   good source. Below each bot message: small thumbs-up/thumbs-down icons.
   Bottom: sticky auto-growing composer with a hint line "Ask in any
   language — English, Hindi, Hinglish, Odia".
3. Empty conversation state — three tappable example-query chips, each
   written in a different language (English, Hindi, Hinglish), instead of
   an illustration or mascot.

Explicitly avoid: rounded chat bubbles, purple/blue gradients, generic
robot/mascot illustrations, animated typing-bubble skeuomorphs, hairline
newspaper-column layouts, zero-border-radius broadsheet styling.

Export a DESIGN.md token file alongside the screens.
```

### 5.2 Stitch prompt — Admin + Super Admin flow
```
Design a multi-screen admin web app for the same "[Your institution]
Information Desk" chatbot product — the admin side where staff manage the
document knowledge base the chatbot answers from.

Use the SAME design tokens as the student-facing app for consistency:
background #EFF1EC, ink indigo #1F2B4D, turmeric gold #D9A62E, banyan green
#2F5D50, slate #8A8F98, alert rust #B5482E. Fraunces for page titles only,
Inter for body, IBM Plex Mono for all numeric/status/ID data.

Layout direction: a dense REGISTRY-TABLE aesthetic (like an official ledger),
not a card-grid dashboard. Thin slate hairlines between rows, no drop
shadows, no rounded card containers for the tables.

Screens to design:
1. Document Library — table with columns Document, Department, Language,
   Version, Status, Uploaded, Actions. Status renders as a small text tag:
   PENDING/VALIDATED in slate, APPROVED in turmeric-gold, INDEXED in
   banyan-green, SUPERSEDED struck through in slate. Row actions: Approve,
   Supersede, Delete (delete opens a confirm step requiring the admin to
   type the filename). "Upload document" button top-right. Filter bar for
   department/language/status.
2. Upload flow — drag-and-drop zone for a PDF, metadata form (department,
   language, version) shown after file selection, then a progress indicator
   naming the real pipeline stages: "Extracting text → Chunking →
   Generating embeddings → Awaiting approval" — not a generic spinner.
3. Unanswered Queries — list of questions the chatbot couldn't answer, each
   with query text, detected language, timestamp, and two actions per row:
   "Mark as needs new document" and "Dismiss (out of scope)". Frame this as
   an actionable backlog at the top of the screen.
4. Analytics dashboard — four plain stat tiles with large monospace numerals
   (Total queries, Successful-retrieval rate, Fallback rate, P95 latency),
   no icons on the tiles, plus two simple bar charts: queries by language,
   and top topics by retrieval frequency.
5. Super Admin — Users & Languages — an admin-accounts table (name, email,
   role, created date) with "Add admin" button, and a supported-languages
   list where each entry shows the language name written in its own script
   next to the English name.

Explicitly avoid: colorful dashboard card grids, gauge/donut chart cliches,
gradient KPI tiles, generic dashboard iconography.

Export a DESIGN.md token file alongside the screens, consistent with the
student-facing app's design tokens.
```

---

## 6. Antigravity missions — wiring the Stitch output to the backend

Dispatch these **after** the Stitch design has been pulled into `/frontend` via the MCP connector (or exported/unzipped). These extend Missions I and J from `02_PRD_Antigravity.md` Section 12 — don't redo the visual design here, only wire behavior.

**Mission L — Wire auth + chat screens to the backend**
> "The `/frontend` directory now contains the Stitch-generated Auth and Chat screens with a `DESIGN.md` token file. Do not change the visual design. Wire every interactive element to the real backend per the Component → Endpoint table in `03_UI_PRD_Stitch.md` Section 4 (IDs C-01 through C-11): login/register calls, sending a chat message, rendering `detected_language`, `sources[]`, `confidence`, and `is_fallback` from the real `/api/v1/chat` response into the existing stamp-badge component, and feedback submission. Remove any placeholder/mock data the Stitch export shipped with. If a needed field (`message_id`, `sources[].excerpt`) is missing from the current backend response, add it to both the FastAPI response model and `/contracts`, and note the change in your walkthrough."
- **Acceptance:** Sending a real message renders a real grounded or fallback stamp badge from live backend data; thumbs-up/down persists to the `feedback` table; no console errors on a full conversation flow.

**Mission M — Wire admin screens to the backend**
> "Wire the Stitch-generated Admin screens (Document Library, Upload flow, Unanswered Queries, Analytics, Super Admin) to the endpoints in `03_UI_PRD_Stitch.md` Section 4 (IDs C-12 through C-26), preserving the exact visual design. Implement the upload flow's progress indicator by polling `GET /api/v1/admin/documents/{id}/status` every 2–3 seconds. Add the two missing endpoints flagged in Section 4 (`GET /api/v1/conversations`, `PATCH /api/v1/admin/unanswered-queries/{id}`) to the FastAPI backend and `/contracts` if they don't exist yet, then wire the UI to them."
- **Acceptance:** Uploading a real PDF through the UI moves it through `pending → validated → approved → indexed` and it becomes answerable in the chat UI end-to-end, with no manual API calls outside the UI.

**Mission N — Multilingual rendering pass**
> "Verify that Devanagari (Hindi) and Odia script text renders correctly in the Chat screen using the Noto Sans/Serif fallback fonts specified in `DESIGN.md`, across message cards, the language-detected pill, and the language management screen. Fix any font-fallback, line-height, or text-clipping issues specific to non-Latin scripts."
- **Acceptance:** A live conversation conducted entirely in Hindi and one entirely in Odia both render with no clipped text, no fallback to a mismatched system font, and correct right-to-left/line-height behavior where applicable.

---

## 7. Anti-slop checklist (run before accepting any UI Artifact)

- [ ] No rounded chat bubbles — message cards are rectangular with a colored left border
- [ ] No purple/blue gradient anywhere (hero, buttons, backgrounds)
- [ ] No generic robot/mascot illustration in empty states — replaced with actionable text or example chips
- [ ] No animated typing-bubble skeuomorph — static three-dot "thinking" indicator only
- [ ] No decorative icons on analytics stat tiles — numerals + labels only
- [ ] Every grounded answer shows the stamp badge; every fallback answer shows the dashed "unverified" variant — never neither, never both
- [ ] Background is `#EFF1EC`, not a warm cream — confirm against `DESIGN.md`, don't eyeball it
- [ ] All copy follows active-voice, plain-language conventions (e.g. "Approve," not "Submit for approval processing"; error banners state what happened and how to fix it, never a raw status code)
- [ ] Every element in Section 4's table fires a real network call in the browser dev tools — nothing still reads from local mock data
