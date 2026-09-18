# SDD Orchestrator — Implementation Specification

> **PySide6 desktop application** for managing Spec-Driven
> Development processes. Orchestrator for knowledge base (wiki), codebase analysis, and
> specification generation/management via OpenSpec.
>
> Document enriched with the source code analysis of **LLM Wiki Info**
> (`llm_wiki-main/`) — React/Tailwind frontend and Rust/Tauri backend.

---

## 1. Vision and Goals

| ID   | Goal                                                                   |
| ---- | ---------------------------------------------------------------------- |
| G1   | Provide a unified desktop interface for the SDD workflow               |
| G2   | Manage knowledge base wiki with navigation, imports, and LLM chat      |
| G3   | Analyze local codebases and visualize dependency graphs                |
| G4   | Generate, edit, validate, and version OpenSpec specifications          |
| G5   | Orchestrate local AI CLIs (Codex, Copilot, Gemini CLI, Claude, etc.)   |

---

## 2. Technology Stack

| Layer             | Technology                                      |
| ----------------- | ----------------------------------------------- |
| **UI Framework**  | PySide6 (Qt 6)                                  |
| **Language**      | Python 3.11+                                    |
| **Theming**       | Global QSS (`dark-theme.qss`)                   |
| **Concurrency**   | QThread / QRunnable / QThreadPool               |
| **Graphs**        | QWebEngineView + Sigma.js / D3.js (like LLM Wiki) |
| **LLM**           | Subprocess CLI (gemini, claude, copilot, codex) |
| **Markdown**      | python-markdown + frontmatter (like LLM Wiki)   |
| **Packaging**     | PyInstaller / Nuitka (future)                   |
| **Testing**       | pytest + pytest-qt                              |

---

## 3. Riferimento Visivo — Analisi LLM Wiki Info

### 3.1 Architettura Frontend LLM Wiki

LLM Wiki è un'app **React + Tailwind v4 + Tauri v2** con questa struttura:

```
src/
├── App.tsx                    # Orchestratore principale
├── main.tsx                   # Entry point (tema, piattaforma)
├── index.css                  # Tailwind v4, OKLCH colors, Geist font
├── components/
│   ├── layout/                # Shell layout & navigazione
│   │   ├── app-layout.tsx     # Layout 3-4 colonne resizable
│   │   ├── icon-sidebar.tsx   # Rail icone 48px (far-left)
│   │   ├── sidebar-panel.tsx  # Pannello espandibile (Knowledge/Files)
│   │   ├── content-area.tsx   # Switch dinamico viste
│   │   ├── research-panel.tsx # Slide-over destro (Deep Research)
│   │   ├── activity-panel.tsx # Drawer bottom (ingest queue)
│   │   ├── knowledge-tree.tsx # Albero semantico wiki
│   │   └── file-tree.tsx      # Esplora filesystem
│   ├── chat/                  # Interfaccia conversazionale
│   │   ├── chat-panel.tsx     # Vista chat completa
│   │   ├── chat-input.tsx     # Input con @ mention e / skills
│   │   ├── chat-message.tsx   # Bolle messaggio + tool stages
│   │   └── reference-knowledge-graph.tsx  # Mini grafo citazioni
│   ├── editor/                # Editor wiki (Milkdown WYSIWYG)
│   ├── graph/                 # Sigma.js knowledge graph
│   ├── review/                # Human-in-the-loop review
│   ├── search/                # Ricerca semantica RRF
│   └── settings/              # 17 sezioni configurazione
├── stores/                    # Zustand global state
│   ├── wiki-store.ts          # Stato centrale, activeView, configs
│   ├── chat-store.ts          # Conversazioni, messaggi, agent modes
│   └── ...
└── lib/                       # Algoritmi, pipeline, transport
```

### 3.2 Layout LLM Wiki — Dimensioni Esatte

```
┌────────────────────────────────────────────────────────────────────────┐
│                     UpdateBanner (opzionale, full-width)               │
├────┬──────────────────────┬─────────────────────────┬──────────────────┤
│    │   Left Sidebar Panel │                         │  Research Panel  │
│ I  │   (150-400px,        │       Content Area      │  (slide-over,   │
│ c  │    default 220px)    │   (flex-1, min-w-0)     │   250px-50%,    │
│ o  │                      │                         │   default 400px)│
│ n  ├──────────────────────┤                         │                 │
│    │  Tabs:               │  Switch by activeView:  │  Attivo solo su │
│ S  │  • Knowledge Tree    │  • ChatPanel            │  viste "embed": │
│ i  │  • File Tree         │  • PreviewPanel (Wiki)  │  wiki, sources, │
│ d  │                      │  • SourcesView          │  search, graph, │
│ e  ├──────────────────────┤  • SearchView           │  lint, review   │
│ b  │  Activity Panel      │  • GraphView            │                 │
│ a  │  (bottom drawer):    │  • LintView             │  Nascosto su    │
│ r  │  • Ingest Queue      │  • ReviewView           │  viste standalone│
│    │  • File Sync Status  │  • SettingsView         │  chat, settings,│
│ 48 │  • Background Tasks  │  • SkillsView           │  skills         │
│ px │                      │                         │                 │
└────┴──────────────────────┴─────────────────────────┴──────────────────┘
```

**Regole di visibilità:**
- **Viste standalone** (`chat`, `skills`, `settings`): sidebar e research panel nascosti → content area usa 100% width accanto al rail 48px
- **Viste embedded** (`wiki`, `sources`, `search`, `graph`, `lint`, `review`): sidebar visibile, research panel opzionale

### 3.3 Navigazione LLM Wiki — Icone e Viste

#### Sezione Top (Viste Principali):
| Icona Lucide       | Vista ID    | Descrizione                              | Badge            |
| ------------------ | ----------- | ---------------------------------------- | ---------------- |
| `MessageSquare`    | `chat`      | Chat agent & Q&A                        | —                |
| `FileText`         | `wiki`      | Lettura/editing wiki                     | —                |
| `FolderOpen`       | `sources`   | Gestione documenti raw                   | —                |
| `Search`           | `search`    | Ricerca full-text + semantica RRF        | —                |
| `Network`          | `graph`     | Knowledge graph 2D interattivo           | —                |
| `ClipboardCheck`   | `lint`      | Validazione struttura wiki               | —                |
| `ClipboardList`    | `review`    | Coda review human-in-the-loop            | Count pendenti   |
| `Globe`            | *(toggle)*  | Deep Research panel                      | Task attivi      |
| `Sparkles`         | `skills`    | Libreria agent skills                    | —                |

#### Sezione Bottom (Sistema):
| Icona/Elemento      | Azione               | Dettagli                                  |
| -------------------- | -------------------- | ----------------------------------------- |
| Dot pulsante colorato | Status daemon        | Verde=ok, Ambra=starting, Rosso=errore    |
| `Settings`           | `settings`           | Cmd+, shortcut. Dot rosso se update dispo |
| `ArrowLeftRight`     | Switch progetto      | Torna a Welcome/Project Picker            |

### 3.4 Struttura Chat LLM Wiki — Dettaglio Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Chat Panel                                                              │
├──────────────┬────────────────────────────┬─────────────────────────────┤
│ Conversation │    Messages Scroll Area    │  Context Details Panel      │
│ Sidebar      │                            │  (min 320px, max 56%,       │
│ (200px)      │  ┌─────────────────────┐   │   default 420px)            │
│              │  │ 🧑 User bubble     │→  │                             │
│ [+ New Chat] │  │   (right-aligned)    │   │  • Cited knowledge items   │
│              │  └─────────────────────┘   │  • Token estimation        │
│ Conv. 1  ●3  │  ┌─────────────────────┐   │  • Categories: wiki, graph,│
│ Conv. 2  ●1  │  │ 🤖 Assistant bubble│←  │    web, anytxt, workspace  │
│ Conv. 3  ●5  │  │   (left-aligned)     │   │  • Mini ReferenceGraph     │
│              │  │   ▸ Tool stages      │   │                             │
│              │  │   ▸ File diffs       │   ├─────────────────────────────┤
│              │  │   ▸ Citations        │   │  Reference Preview Panel   │
│              │  └─────────────────────┘   │  (wiki page live preview)  │
│              │                            ├─────────────────────────────┤
│              │  ┌─────────────────────┐   │  Generated Outputs Panel   │
│              │  │ 📝 Input Area      │   │  (280px, file/artifact list)│
│              │  │  [@file] [/skill]   │   │                             │
│              │  │  [📎][🌐][⚡][📤]  │   │                             │
│              │  └─────────────────────┘   │                             │
└──────────────┴────────────────────────────┴─────────────────────────────┘
```

**Bolla Utente:** allineata a destra, max 80%, avatar circolare `User`, sfondo accent
**Bolla Assistente:** allineata a sinistra, max 80%, avatar `Bot`, sfondo muted
  - Tool stages collassabili (understanding → routing → tool_call → result)
  - Shell command approval banner (ambra, con bottone "Approve")
  - Inline diff reviewer con undo single-click
  - Markdown + LaTeX + Mermaid + wikilinks
  - Citations panel con source pills

**Input Area:**
  - `@` → popup file context, `/` → popup skills
  - Textarea auto-growing (max 120px)
  - Chip attivi: immagini, context files (blu), skills (verde)
  - Toolbar: Attach Image, Web Search toggle, AnyTxt toggle, Skills popover
  - Dropdown: Retrieval Mode (Standard/Smart/Faithful), Agent Mode (Fast/Standard/Deep/Local)
  - Send/Stop button

### 3.5 Backend LLM Wiki — CLI Discovery (Logica Chiave)

L'app LLM Wiki risolve un problema critico: le app desktop lanciate da Finder/Dock
su macOS ereditano un `$PATH` minimale (solo `/usr/bin:/bin`) che NON include tool
installati via `nvm`, `asdf`, `fnm`, Homebrew, ecc.

**Pipeline di risoluzione (`cli_resolver.rs`):**

1. **Cache check**: HashMap in-memory `RESOLVED_COMMANDS`. Se il path cached esiste su disco → ritorna subito; se eliminato → invalida cache.
2. **Windows**: testa candidati `["claude.cmd", "claude.exe", "claude"]` via `which::which()`
3. **macOS/Linux — Step 1**: `which::which(command)` con `$PATH` ereditato
4. **macOS/Linux — Step 2 (Fallback)**: Probe della login shell interattiva:
   - Legge `$SHELL` (default `/bin/sh`)
   - Shell minimali (`sh`, `dash`): flag `-ic`
   - Shell complete (`zsh`, `bash`, `fish`): flag `-ilc` (interactive + login)
   - Comando: `printf '\036PATH=%s\036\n' "$PATH"` (delimitatore `\x1e` record separator)
   - **Timeout 10 secondi** per evitare hang
   - Risultato cached in `RESOLVED_SHELL_PATH`
5. **Step 3**: `which::which_in(command, shell_path)` con il PATH completo
6. **Step 4**: Cache del `PathBuf` risolto

**CLI cercate in LLM Wiki:**

| Tool       | Candidati Windows          | Uso                  | Verifica              |
| ---------- | -------------------------- | -------------------- | --------------------- |
| `claude`   | `claude.cmd`, `claude.exe` | Claude Code CLI      | `claude --version`    |
| `codex`    | `codex.cmd`, `codex.exe`   | OpenAI Codex CLI     | `codex --version`     |

**Per SDD Orchestrator estendiamo a 8+ CLI** (vedi §5.2).

### 3.6 Backend LLM Wiki — Provider LLM e Agent Loop

**8 Provider supportati:**
1. `openai` — API HTTP diretta
2. `anthropic` — API con prompt caching e thinking budgets
3. `azure` — Azure OpenAI endpoints
4. `google` — Gemini API
5. `ollama` — Server locale
6. `minimax` — Endpoint Anthropic-compatible
7. `custom` — Endpoint custom (mode: `openai` o `anthropic_messages`)
8. `claude-code` / `codex-cli` — Subprocess CLI con JSON streaming IPC

**Agent Loop**: max **8 iterazioni** tool-calling. Tools disponibili:
`wiki.search`, `wiki.read_page`, `wiki.write_page`, `graph.search`,
`source.search`, `web.search`, `shell.exec`, `workspace.write_file`

### 3.7 Backend LLM Wiki — Struttura Workspace

```
<project_root>/
├── raw/
│   ├── sources/             # PDF, docs, web clips importati
│   └── assets/              # Allegati e binari
├── wiki/
│   ├── entities/            # Entità (modelli, tool, aziende, persone)
│   ├── concepts/            # Idee, tecniche, concetti matematici
│   ├── sources/             # Note letteratura & sommari
│   ├── queries/             # Domande di ricerca aperte
│   ├── comparisons/         # Analisi comparative
│   ├── synthesis/           # Conclusioni cross-cutting
│   ├── index.md             # Indice categorizzato
│   ├── log.md               # Log cronologico inverso
│   └── overview.md          # Overview alto livello
├── schema.md                # Contratto schema progetto
├── purpose.md               # Obiettivo ricerca
├── agent-workspace/         # File generati dall'agente
├── .obsidian/               # Compatibilità Obsidian vault
└── .llm-wiki/               # Metadata interni (nascosti)
    ├── project.json         # UUID progetto
    ├── lancedb/             # Database vettoriale
    ├── agent-sessions/      # Storico chat per sessione
    ├── skills/              # Skills progetto-locali
    └── file-history/        # Backup revisioni file
```

### 3.8 Palette Colori LLM Wiki (OKLCH → HEX)

#### Dark Theme:
| Token CSS                | OKLCH                          | HEX Appross. | Uso                        |
| ------------------------ | ------------------------------ | ------------ | -------------------------- |
| `--background`           | `oklch(0.16 0.005 260)`       | `#1a1b1e`    | Sfondo principale          |
| `--card` / `--popover`   | `oklch(0.205 0.005 260)`      | `#25262b`    | Card, pannelli elevati     |
| `--muted`                | `oklch(0.269 0.005 260)`      | `#2c2e33`    | Container dark, input      |
| `--border`               | `oklch(1 0 0 / 12%)`          | `#373a40`    | Bordi (12% white opacity)  |
| `--foreground`           | `oklch(0.985 0 0)`            | `#f8f9fa`    | Testo principale           |
| `--muted-foreground`     | `oklch(0.708 0 0)`            | `#909296`    | Testo secondario           |
| `--primary`              | `oklch(0.922 0 0)`            | `#e9ecef`    | Accent (bianco caldo)      |
| `--primary-foreground`   | `oklch(0.205 0 0)`            | `#25262b`    | Testo su primary           |
| `--destructive`          | `oklch(0.704 0.191 22.216)`   | `#fa5252`    | Errori, delete             |

#### Light Theme:
| Token CSS                | OKLCH                          | HEX Appross. | Uso                        |
| ------------------------ | ------------------------------ | ------------ | -------------------------- |
| `--background`           | `oklch(1 0 0)`                | `#ffffff`    | Sfondo                     |
| `--foreground`           | `oklch(0.145 0 0)`            | `#212529`    | Testo                      |
| `--primary`              | `oklch(0.205 0 0)`            | `#25262b`    | Accent (charcoal)          |
| `--muted`                | `oklch(0.97 0 0)`             | `#f1f3f5`    | Grigio chiaro              |

**Font:** Geist Variable, sans-serif (14px base, scaling via rem)
**Theming:** 3 modi — `light`, `dark`, `system` (media query listener)

---

## 4. Architettura MVC — Struttura File (SDD Orchestrator)

```
sdd-orchestrator/
├── main.py                        # Entry point, QApplication, QSS loading
├── styles/
│   └── dark-theme.qss             # Foglio di stile globale (§6)
├── assets/
│   ├── icons/                     # SVG/PNG per sidebar e toolbar
│   └── fonts/                     # Font custom (opzionale)
├── models/
│   ├── __init__.py
│   ├── workspace_model.py         # RF1  — Logica workspace/init
│   ├── cli_discovery_model.py     # RF11 — Ricerca CLI AI (con login shell probe)
│   ├── wiki_model.py              # RF2, RF5 — Import docs, navigazione wiki
│   ├── chat_model.py              # RF4  — Chat LLM con wiki
│   ├── search_model.py            # RF3  — Ricerca semantica
│   ├── codebase_model.py          # RF7  — Analisi codebase
│   ├── graph_model.py             # RF8, RF9 — Parsing grafo
│   ├── openspec_model.py          # RF12-RF17 — Ciclo vita OpenSpec
│   └── agent_model.py             # RF10 — Selezione agenti
├── controllers/
│   ├── __init__.py
│   ├── workspace_controller.py    # RF1  — Mediatore workspace
│   ├── cli_controller.py          # RF11 — Mediatore CLI discovery
│   ├── wiki_controller.py         # RF2, RF5 — Mediatore wiki
│   ├── chat_controller.py         # RF4  — Mediatore chat
│   ├── search_controller.py       # RF3  — Mediatore ricerca
│   ├── codebase_controller.py     # RF7  — Mediatore analisi
│   ├── graph_controller.py        # RF8, RF9 — Mediatore grafo
│   ├── openspec_controller.py     # RF12-RF17 — Mediatore OpenSpec
│   └── agent_controller.py        # RF10 — Mediatore agenti
├── views/
│   ├── __init__.py
│   ├── main_window.py             # QMainWindow principale
│   ├── sidebar.py                 # Icon sidebar (48px) + sidebar panel espandibile
│   ├── workspace_view.py          # RF1  — Welcome screen / pannello workspace
│   ├── cli_status_view.py         # RF11 — Stato CLI trovate
│   ├── wiki_browser_view.py       # RF5  — KnowledgeTree + reader (come LLM Wiki)
│   ├── wiki_import_view.py        # RF2  — Dialogo importazione (drag-and-drop)
│   ├── chat_view.py               # RF4  — Chat panel completo (come LLM Wiki)
│   ├── search_bar_view.py         # RF3  — Barra ricerca globale
│   ├── codebase_view.py           # RF7  — Pannello analisi
│   ├── graph_view.py              # RF8, RF9 — QWebEngineView grafo (Sigma.js)
│   ├── openspec_editor_view.py    # RF13 — Editor specifiche split
│   ├── openspec_stepper_view.py   # RF17 — Stepper workflow 5 fasi
│   ├── openspec_export_view.py    # RF16 — Dialogo export
│   ├── openspec_history_view.py   # RF15 — Pannello versioning
│   ├── agent_selector_view.py     # RF10 — Dropdown agenti
│   ├── settings_view.py           # Settings (tabbed, come LLM Wiki)
│   └── widgets/
│       ├── __init__.py
│       ├── chat_bubble.py         # Widget bolla messaggio (user/assistant)
│       ├── chat_input.py          # Input area con toolbar (come LLM Wiki)
│       ├── conversation_sidebar.py # Lista conversazioni (come LLM Wiki)
│       ├── stepper_widget.py      # Widget stepper generico
│       ├── status_indicator.py    # Indicatore stato (dot pulsante colorato)
│       ├── file_drop_area.py      # Area drag-and-drop file
│       ├── collapsible_section.py # Sezione sidebar collassabile
│       ├── tool_stage_widget.py   # Stage tool execution (understanding→result)
│       └── activity_panel.py      # Bottom drawer per task queue
├── workers/
│   ├── __init__.py
│   ├── base_worker.py             # QThread base riusabile
│   ├── cli_scan_worker.py         # RF11 — Thread scansione CLI
│   ├── import_worker.py           # RF2  — Thread import documenti
│   ├── chat_worker.py             # RF4  — Thread invocazione LLM (streaming)
│   ├── codebase_worker.py         # RF7  — Thread analisi codebase
│   ├── openspec_worker.py         # RF12 — Thread generazione specs
│   └── validation_worker.py       # RF14 — Thread validazione
├── utils/
│   ├── __init__.py
│   ├── paths.py                   # Costanti path SDD
│   ├── shell_path_resolver.py     # Login shell PATH probe (da LLM Wiki)
│   ├── markdown_parser.py         # Parser index.md → struttura ad albero
│   ├── file_utils.py              # Operazioni file sicure
│   └── config.py                  # Configurazione persistente (QSettings)
└── tests/
    ├── __init__.py
    ├── test_workspace_model.py
    ├── test_cli_discovery.py
    ├── test_shell_path_resolver.py
    ├── test_wiki_model.py
    └── test_openspec_model.py
```

---

## 5. Requisiti Funzionali — Specifiche di Implementazione

### 5.1 RF1 — Inizializzazione Workspace

**Struttura SDD** (ispirata a LLM Wiki ma adattata a OpenSpec):

```
<workspace_root>/
├── .agents/
│   └── skills/                    # Definizioni skill agente
├── knowledge-base/
│   ├── AGENTS.md                  # Convenzioni wiki
│   ├── index.md                   # Indice categorizzato (come wiki/index.md in LLM Wiki)
│   ├── log.md                     # Log cronologico (come wiki/log.md in LLM Wiki)
│   ├── raw/                       # Documenti grezzi importati (come raw/sources/)
│   │   └── processed/             # Sorgenti processati
│   └── pages/                     # Pagine wiki (come wiki/{entities,concepts,...})
│       ├── entities/
│       ├── concepts/
│       ├── sources/
│       ├── decisions/
│       └── questions/
├── openspec/
│   ├── config.yaml                # Configurazione OpenSpec
│   ├── specs/                     # Specifiche accettate
│   └── changes/                   # Change in-flight
├── graphify-out/                  # (opzionale) Output analisi grafo
│   ├── graph.json
│   └── GRAPH_REPORT.md
└── AGENTS.md                      # Contratto agente progetto
```

**Validazione** (ispirata a `validate_wiki_project_root` di LLM Wiki che richiede `schema.md` + `wiki/`):
- Per SDD: richiesti `knowledge-base/` (dir) + `openspec/` (dir) + `AGENTS.md` (file)

**Model** (`workspace_model.py`):
```python
class WorkspaceModel:
    """Logica pura, zero dipendenze Qt."""

    REQUIRED_DIRS = [
        ".agents/skills",
        "knowledge-base/raw",
        "knowledge-base/raw/processed",
        "knowledge-base/pages",
        "knowledge-base/pages/entities",
        "knowledge-base/pages/concepts",
        "knowledge-base/pages/sources",
        "knowledge-base/pages/decisions",
        "knowledge-base/pages/questions",
        "openspec/specs",
        "openspec/changes",
    ]
    REQUIRED_FILES = {
        "knowledge-base/index.md": "# Knowledge Base Index\n\n## Categories\n...",
        "knowledge-base/log.md": "# Knowledge Base Log\n",
        "knowledge-base/AGENTS.md": "# Wiki Conventions\n",
        "openspec/config.yaml": "version: 1\n",
        "AGENTS.md": "# Agent Contract\n",
    }

    def validate_workspace(self, path: str) -> dict:
        """Ritorna {valid: bool, missing_dirs: [], missing_files: [],
                    stats: {wiki_pages: int, specs: int, changes: int}}"""

    def initialize_workspace(self, path: str) -> bool:
        """Crea la struttura SDD completa. Ritorna True se successo."""

    def get_workspace_info(self, path: str) -> dict:
        """Ritorna metadati: nome, num pagine wiki, num specs, ultimo accesso."""

    def has_graphify_data(self, path: str) -> bool:
        """Check esistenza graphify-out/graph.json."""
```

**Controller** (`workspace_controller.py`):
```python
class WorkspaceController(QObject):
    workspace_opened = Signal(str)           # path
    workspace_validated = Signal(dict)        # validation result
    workspace_initialized = Signal(str)       # path
    workspace_error = Signal(str)             # error message
    workspace_stats_ready = Signal(dict)      # workspace info/stats

    def open_workspace(self, path: str) -> None: ...
    def initialize_workspace(self, path: str) -> None: ...
    def validate_workspace(self, path: str) -> None: ...
```

**View** (`workspace_view.py`):
```python
class WorkspaceView(QWidget):
    """Welcome screen / pannello workspace (ispirato a LLM Wiki welcome-screen.tsx)."""

    # Welcome Screen (quando nessun workspace aperto):
    #   Logo + titolo "SDD Orchestrator"
    #   [Open Workspace] button → QFileDialog.getExistingDirectory()
    #   [Recent Workspaces] lista con path + stats (come LLM Wiki recent projects)
    #
    # Workspace Info Panel (dopo apertura):
    #   Card riepilogo: nome, path, num pagine wiki, num specs, CLI status
    #   Quick actions: [Import Docs] [New Change] [Analyze Codebase]
```

**Flusso:**
```
1. App avviata → WorkspaceView mostra Welcome Screen
2. Utente clicca "Open Workspace" → QFileDialog
3. WorkspaceView emette open_requested(path) signal
4. WorkspaceController.open_workspace(path)
   → model.validate_workspace(path)
5. Se valido → workspace_opened(path) → MainWindow carica tutte le viste
6. Se non valido → workspace_validated({valid: False, missing: [...]})
   → Vista mostra QMessageBox: "Struttura SDD non trovata. Inizializzare?"
   → Se sì → controller.initialize_workspace(path)
   → workspace_initialized(path) → auto-scan CLI → carica wiki
```

---

### 5.2 RF11 — Ricerca CLI AI

**Implementazione ispirata a `cli_resolver.rs` di LLM Wiki**, adattata in Python.

**Il problema:** Su macOS, le app desktop lanciate dal Finder ereditano un `$PATH` minimale (`/usr/bin:/bin`) che non include tool installati via Homebrew, nvm, asdf, etc.

**Soluzione: Login Shell PATH Probe** (come LLM Wiki):

```python
# utils/shell_path_resolver.py

import os
import subprocess
import shutil
from functools import lru_cache

LOGIN_SHELL_TIMEOUT = 10  # secondi (come LLM Wiki)
RECORD_SEP = "\x1e"       # delimitatore framing (come LLM Wiki)

@lru_cache(maxsize=1)
def resolve_login_shell_path() -> str:
    """Probe la login shell interattiva per ottenere il PATH completo.
    Ispirato a cli_resolver.rs login_shell_path().
    """
    shell = os.environ.get("SHELL", "/bin/sh")
    shell_name = os.path.basename(shell)

    # Shell minimali: -ic, shell complete: -ilc (come LLM Wiki)
    if shell_name in ("sh", "dash", "ash"):
        flags = ["-ic"]
    else:
        flags = ["-ilc"]

    # Usa record separator \x1e per isolare PATH da MOTD/banner
    cmd = f"printf '{RECORD_SEP}PATH=%s{RECORD_SEP}\\n' \"$PATH\""

    try:
        result = subprocess.run(
            [shell] + flags + [cmd],
            capture_output=True, text=True,
            timeout=LOGIN_SHELL_TIMEOUT,
            env={**os.environ, "LC_ALL": "C"}
        )
        # Estrai PATH tra i delimitatori \x1e
        output = result.stdout
        start = output.find(f"{RECORD_SEP}PATH=")
        end = output.find(RECORD_SEP, start + 1)
        if start >= 0 and end > start:
            return output[start + len(f"{RECORD_SEP}PATH="):end]
    except (subprocess.TimeoutExpired, OSError):
        pass

    return os.environ.get("PATH", "")


def find_cli_command(command: str, candidates: list[str] | None = None) -> str | None:
    """Cerca un comando CLI con fallback alla login shell PATH.
    Pipeline identica a LLM Wiki find_cli_command().
    """
    # Step 1: shutil.which con PATH corrente
    path = shutil.which(command)
    if path:
        return path

    # Step 1b: Candidati alternativi (Windows-style)
    if candidates:
        for candidate in candidates:
            path = shutil.which(candidate)
            if path:
                return path

    # Step 2: Fallback - login shell PATH probe
    full_path = resolve_login_shell_path()
    if full_path:
        # Cerca nel PATH completo
        for directory in full_path.split(os.pathsep):
            full = os.path.join(directory, command)
            if os.path.isfile(full) and os.access(full, os.X_OK):
                return full

    return None
```

**CLI Registry** (estensione di LLM Wiki che cerca solo `claude` e `codex`):

| CLI Key        | Binary Name      | Display Name      | Verifica                | Tipo           |
| -------------- | ---------------- | ----------------- | ----------------------- | -------------- |
| `claude`       | `claude`         | Claude Code       | `claude --version` (3s) | Anthropic CLI  |
| `codex`        | `codex`          | OpenAI Codex      | `codex --version` (3s)  | OpenAI CLI     |
| `gemini`       | `gemini`         | Gemini CLI        | `gemini --version`      | Google CLI     |
| `agy`          | `agy`            | Antigravity       | `agy --version`         | Google CLI     |
| `aider`        | `aider`          | Aider             | `aider --version`       | Open Source    |
| `gh-copilot`   | `gh`             | GitHub Copilot    | `gh copilot --version`  | GitHub/MS      |
| `ollama`       | `ollama`         | Ollama (local)    | `ollama list`           | Local LLM      |
| `continue`     | `continue`       | Continue.dev      | —                       | IDE Extension  |

**Model** (`cli_discovery_model.py`):
```python
@dataclass
class CLIInfo:
    key: str
    binary_name: str
    display_name: str
    found: bool
    path: str | None
    version: str | None
    cli_type: str          # "anthropic", "openai", "google", "local", etc.

class CLIDiscoveryModel:
    """Scansione filesystem per CLI AI. Nessuna dipendenza Qt.
    Usa shell_path_resolver per la logica di discovery ispirata a LLM Wiki."""

    CLI_REGISTRY: list[dict] = [...]  # tabella sopra

    def scan_all(self) -> list[CLIInfo]:
        """Itera ogni CLI, usa find_cli_command() con login shell fallback."""

    def scan_single(self, key: str) -> CLIInfo:
        """Scansione singola CLI con version check (timeout 3s come LLM Wiki)."""

    def get_version(self, binary_path: str, version_flag: str = "--version") -> str | None:
        """Esegue `binary --version` con timeout 3s (come claude_cli_detect/codex_cli_detect)."""
```

**Worker** (`cli_scan_worker.py`):
```python
class CLIScanWorker(QThread):
    """Esegue la scansione CLI in background. MAI sul main thread.
    Il login shell probe può richiedere fino a 10 secondi."""

    cli_found = Signal(object)        # singola CLIInfo trovata
    scan_progress = Signal(int, int)  # (current, total)
    scan_complete = Signal(list)      # lista completa CLIInfo
    scan_error = Signal(str)

    def run(self):
        results = []
        for i, cli_def in enumerate(self._model.CLI_REGISTRY):
            info = self._model.scan_single(cli_def["key"])
            self.cli_found.emit(info)
            self.scan_progress.emit(i + 1, len(self._model.CLI_REGISTRY))
            results.append(info)
        self.scan_complete.emit(results)
```

**Controller** (`cli_controller.py`):
```python
class CLIController(QObject):
    cli_scan_started = Signal()
    cli_found = Signal(object)           # CLIInfo
    cli_scan_progress = Signal(int, int)
    cli_scan_complete = Signal(list)     # list[CLIInfo]
    cli_scan_error = Signal(str)

    def start_scan(self) -> None:
        """Lancia CLIScanWorker in background."""

    def get_available_agents(self) -> list[CLIInfo]:
        """Ritorna solo CLI con found=True."""
```

**View** (`cli_status_view.py`):
```python
class CLIStatusView(QWidget):
    """Status CLI, ispirato al daemon status dot di LLM Wiki icon-sidebar.tsx."""

    # Card per ogni CLI: icona + nome + status indicator
    #   ✅ Verde pulsante = found (con versione)
    #   ❌ Grigio = not found
    #   🟡 Ambra pulsante = scanning in corso
    # Progress bar durante scansione
    # Pulsante "Rescan"
```

---

### 5.3 RF10 — Selezione Agenti

**Ispirato al dropdown Agent Mode di LLM Wiki** (`chat-input.tsx` → Fast/Standard/Deep/Local):

**Model** (`agent_model.py`):
```python
@dataclass
class AgentConfig:
    cli_key: str
    display_name: str
    model_name: str | None     # es. "gpt-4", "claude-sonnet"
    extra_args: list[str]
    cli_type: str              # per raggruppamento nel dropdown

class AgentModel:
    def get_available_agents(self, found_clis: list[CLIInfo]) -> list[AgentConfig]: ...
    def set_active_agent(self, agent: AgentConfig) -> None: ...
    def get_active_agent(self) -> AgentConfig | None: ...
```

**View** (`agent_selector_view.py`):
```python
class AgentSelectorView(QComboBox):
    agent_selected = Signal(object)  # AgentConfig
    # Popola dropdown con agenti raggruppati per tipo CLI
    # Mostra icona/indicator + nome agente + modello
    # Ispirato al dropdown mode di LLM Wiki chat-input
```

---

### 5.4 RF2 — Importazione Documenti

**Ispirato al sistema di import di LLM Wiki** (`source-lifecycle.ts`, `file-sync.ts`):
- Drag-and-drop o selezione file
- Badge stati: `not-ingested`, `queued`, `running`, `ingested`, `error`
- Activity Panel per monitorare la coda

**Model** (`wiki_model.py`):
```python
class WikiModel:
    SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt", ".rst", ".docx"]

    def import_document(self, source_path: str, workspace: str) -> dict:
        """Copia file in knowledge-base/raw/, ritorna metadati."""

    def parse_index(self, workspace: str) -> dict:
        """Legge index.md e ritorna struttura ad albero per categorie."""

    def list_pages(self, workspace: str) -> list[dict]:
        """Lista pagine in knowledge-base/pages/ (ricorsivo per sottocategorie)."""

    def read_page(self, page_path: str) -> str:
        """Legge contenuto pagina markdown."""

    def get_page_frontmatter(self, page_path: str) -> dict:
        """Parsifica YAML frontmatter (come LLM Wiki frontmatter.ts)."""
```

**Worker** (`import_worker.py`):
```python
class ImportWorker(QThread):
    import_progress = Signal(str, int, int)  # filename, current, total
    import_complete = Signal(list)           # imported files
    import_error = Signal(str, str)          # filename, error
```

**View** (`wiki_import_view.py`):
```python
class WikiImportView(QDialog):
    # FileDropArea per drag-and-drop (come LLM Wiki sources view)
    # QFileDialog per selezione multipla
    # Lista file con badge stato (not-ingested → queued → ingested)
    # Progress bar importazione
    # Pulsante "Import All"
```

---

### 5.5 RF5 — Navigazione Wiki

**Ispirato a `knowledge-tree.tsx` + `sidebar-panel.tsx` di LLM Wiki:**

**View** (`wiki_browser_view.py`):
```python
class WikiBrowserView(QWidget):
    """Pannello split come LLM Wiki: KnowledgeTree a sinistra + reader a destra."""

    # QSplitter (horizontal)
    #   ├── QTreeView (knowledge_tree)
    #   │   Raggruppato per tipo pagina (come LLM Wiki):
    #   │   ├── 📦 Entities
    #   │   ├── 💡 Concepts
    #   │   ├── 📄 Sources
    #   │   ├── ❓ Questions
    #   │   └── 🔧 Decisions
    #   └── QWidget (reader_panel)
    #       ├── QWidget (toolbar): [Back] [Forward] [Refresh] [Import] [Frontmatter]
    #       └── QTextBrowser (page_reader) — render Markdown → HTML
    #
    # Come LLM Wiki, ha anche un tab "Files" per vista filesystem grezza
```

---

### 5.6 RF4 — Chat con la Wiki

**Struttura fedelmente ispirata a `chat-panel.tsx` di LLM Wiki:**

**Model** (`chat_model.py`):
```python
@dataclass
class ChatMessage:
    role: str          # "user" | "assistant" | "system"
    content: str
    timestamp: datetime
    sources: list[str] # wiki pages citate
    tool_events: list[dict]  # tool stages (come LLM Wiki AgentTurnActivity)

class ChatModel:
    def build_context(self, workspace: str, query: str) -> str:
        """Costruisce contesto da wiki pages rilevanti."""

    def format_prompt(self, messages: list[ChatMessage], context: str) -> str:
        """Formatta prompt per CLI LLM."""

    def parse_response(self, raw_output: str) -> ChatMessage:
        """Parsifica output CLI in ChatMessage."""

    def save_conversation(self, conv_id: str, messages: list[ChatMessage]) -> None:
        """Persisti conversazione (come LLM Wiki agent-sessions/)."""

    def list_conversations(self) -> list[dict]:
        """Lista conversazioni salvate."""
```

**Worker** (`chat_worker.py`):
```python
class ChatWorker(QThread):
    """Invoca CLI LLM in subprocess con streaming. SEMPRE in background.
    Ispirato a claude_cli_spawn/codex_cli_spawn di LLM Wiki."""

    token_received = Signal(str)        # streaming token (come eventi LLM Wiki)
    tool_stage = Signal(dict)           # tool execution stage update
    response_complete = Signal(object)  # ChatMessage finale
    response_error = Signal(str)

    def run(self):
        # subprocess.Popen con streaming stdout line-by-line
        # Parsifica JSON events (come LLM Wiki stream-json format)
        # Emette token_received per ogni chunk
        # Emette tool_stage per ogni step (understanding, routing, tool_call, result)
```

**View** (`chat_view.py`):
```python
class ChatView(QWidget):
    """Pannello chat completo. Layout 3 colonne come LLM Wiki chat-panel.tsx."""

    # QHBoxLayout
    #   ├── ConversationSidebar (200px fisso)
    #   │   ├── QPushButton ("+ New Chat")
    #   │   └── QListWidget (conversation_list)
    #   │       Per ogni conversazione: titolo, count messaggi, timestamp
    #   │       Hover → bottone delete (come LLM Wiki Trash2)
    #   │
    #   ├── QWidget (main_column, flex-1)
    #   │   └── QVBoxLayout
    #   │       ├── QScrollArea (message_area, auto-scroll)
    #   │       │   └── QVBoxLayout (message_list)
    #   │       │       ├── ChatBubble (user, right-aligned)
    #   │       │       ├── ChatBubble (assistant, left-aligned)
    #   │       │       │   ├── ToolStageWidget (collapsible, come LLM Wiki)
    #   │       │       │   ├── Markdown content
    #   │       │       │   └── Citations panel
    #   │       │       └── StreamingIndicator (typing dots)
    #   │       └── ChatInput (bottom, fixed)
    #   │           ├── QTextEdit (auto-grow, max 120px come LLM Wiki)
    #   │           ├── Chip attivi (context files, skills)
    #   │           └── Toolbar: [📎 Attach] [🌐 Web] [⚡ Mode ▼] [📤 Send/Stop]
    #   │
    #   └── QWidget (context_panel, collapsible, default 420px)
    #       ├── Tab: Cited Knowledge (sources, token count)
    #       ├── Tab: Reference Preview (wiki page reader)
    #       └── Tab: Generated Outputs (file list)
```

**Widgets** (`chat_bubble.py`):
```python
class ChatBubble(QWidget):
    """Bolla messaggio. Stile differenziato come LLM Wiki chat-message.tsx."""

    # User: right-aligned, accent bg, avatar circolare "U"
    # Assistant: left-aligned, muted bg, avatar circolare "🤖"
    # Contenuto: Markdown renderizzato (GFM)
    # Tool stages: accordion collassabile (come LLM Wiki AgentTurnActivity)
    # Citations: pill cliccabili in fondo (come LLM Wiki CitedReferencesPanel)
    # Hover toolbar: [Copy] [Save to Wiki] [Regenerate] (come LLM Wiki)
```

---

### 5.7 RF3 — Ricerca Semantica (NICE TO HAVE)

**Ispirato a `search-view.tsx` di LLM Wiki** (ricerca RRF: lexical + vector + graph):

**Model** (`search_model.py`):
```python
class SearchModel:
    def build_index(self, workspace: str) -> None:
        """Indicizza pagine wiki + specs per ricerca full-text."""

    def search(self, query: str, max_results: int = 20) -> list[dict]:
        """Ricerca full-text. Ritorna [{page, score, snippet, category}]."""
```

**View** (`search_bar_view.py`):
```python
class SearchBarView(QLineEdit):
    """Barra ricerca nella toolbar, con popup risultati live.
    Come LLM Wiki search-view.tsx ma come widget toolbar."""
    search_requested = Signal(str)
    result_selected = Signal(str)  # path pagina
```

---

### 5.8 RF7 — Analisi Codebase

**Model** (`codebase_model.py`):
```python
class CodebaseModel:
    def analyze_structure(self, workspace: str) -> dict:
        """Analizza struttura file/cartelle, linguaggi, stats."""

    def detect_languages(self, workspace: str) -> dict[str, int]:
        """Conta file per linguaggio."""

    def generate_report(self, workspace: str) -> str:
        """Genera report markdown analisi."""
```

**View** (`codebase_view.py`):
```python
class CodebaseView(QWidget):
    # QSplitter
    #   ├── QTreeView (file_tree) — albero filesystem (come LLM Wiki file-tree.tsx)
    #   └── QWidget (report_panel)
    #       ├── Stats cards (num file, linguaggi, LOC)
    #       └── QTextBrowser (report markdown)
```

---

### 5.9 RF8 & RF9 — Visualizzazione Grafo

**Ispirato a `graph-view.tsx` di LLM Wiki** che usa **Sigma.js + Graphology** con
un WebWorker per ForceAtlas2 / Louvain community layout:

**Model** (`graph_model.py`):
```python
class GraphModel:
    def load_graph(self, workspace: str) -> dict | None:
        """Carica graphify-out/graph.json se esiste."""

    def graph_exists(self, workspace: str) -> bool: ...

    def get_node_details(self, node_id: str) -> dict: ...

    def generate_html_visualization(self, graph_data: dict) -> str:
        """Genera HTML con Sigma.js/Graphology (come LLM Wiki graph-view.tsx)
        per rendering in QWebEngineView. Include:
        - ForceAtlas2 layout
        - Community detection (Louvain)
        - Filtri per tipo nodo
        - Ricerca nodo
        - Pan/zoom interattivo"""
```

**View** (`graph_view.py`):
```python
class GraphView(QWidget):
    # QVBoxLayout
    #   ├── QWidget (toolbar)
    #   │   ├── QComboBox (layout_selector: force/tree/radial)
    #   │   ├── QLineEdit (node_search)
    #   │   ├── QComboBox (community_filter)
    #   │   └── QPushButton (refresh)
    #   ├── QWebEngineView (graph_canvas) — render Sigma.js HTML
    #   └── QWidget (details_panel, collapsible)
    #       └── QTextBrowser (node_details: backlinks, outgoing, tags)
    #
    # Fallback: QLabel "Graph data not found" se graph.json non esiste
```

---

### 5.10 RF12 — Generazione Specifiche

**Model** (`openspec_model.py`):
```python
class OpenSpecModel:
    def list_changes(self, workspace: str) -> list[dict]: ...
    def list_specs(self, workspace: str) -> list[dict]: ...
    def read_artifact(self, path: str) -> dict:
        """Legge artifact YAML/MD con frontmatter (come LLM Wiki frontmatter.ts)."""
    def create_change(self, workspace: str, name: str, data: dict) -> str: ...
    def build_cli_command(self, skill: str, workspace: str, args: dict) -> list[str]:
        """Costruisce comando CLI. Usa find_cli_command() per risolvere il binario."""
    def parse_cli_output(self, output: str) -> dict: ...
```

---

### 5.11 RF13 — Editing Assistito

**Ispirato a `wiki-editor.tsx` (Milkdown WYSIWYG) + chat laterale di LLM Wiki:**

**View** (`openspec_editor_view.py`):
```python
class OpenSpecEditorView(QWidget):
    """Editor split: testo + AI assistant. Come LLM Wiki preview-panel + chat."""

    # QSplitter (horizontal)
    #   ├── QWidget (editor_panel)
    #   │   ├── QTabWidget (open_specs) — tab per ogni spec/artifact aperto
    #   │   │   └── QTextEdit (syntax highlighted, con frontmatter panel)
    #   │   └── QWidget (editor_toolbar)
    #   │       ├── QPushButton (save)
    #   │       ├── QPushButton (validate, RF14)
    #   │       ├── QPushButton (export, RF16)
    #   │       └── QPushButton (history, RF15)
    #   └── QWidget (assistant_panel)
    #       ├── ChatView (mini, per suggerimenti AI contestuali)
    #       └── QLabel ("Editing: proposal.md | Change: feature-xyz")
```

---

### 5.12 RF14 — Validazione Coerenza

```python
class OpenSpecModel:
    def validate_change(self, workspace: str, change_name: str) -> dict:
        """Valida coerenza: frontmatter, referenze, completezza.
        Ritorna {valid: bool, errors: [], warnings: []}."""
    def validate_spec(self, workspace: str, spec_path: str) -> dict: ...
```

---

### 5.13 RF15 — Revisione e Versionamento

**Ispirato a `file-history-panel.tsx` di LLM Wiki:**

**View** (`openspec_history_view.py`):
```python
class OpenSpecHistoryView(QWidget):
    # QVBoxLayout
    #   ├── QListWidget (version_list) — lista revisioni con timestamp
    #   │   Per ogni entry: data, autore, snippet diff
    #   └── QTextBrowser (diff_viewer) — diff colorato (add=green, del=red)
    #   └── QPushButton (restore_btn) — ripristina versione selezionata
    #       (come LLM Wiki restore_file_history)
```

---

### 5.14 RF16 — Esportazione

**View** (`openspec_export_view.py`):
```python
class OpenSpecExportView(QDialog):
    # Selezione formato: JSON / Markdown / YAML
    # Checklist specs da esportare
    # Directory output (QFileDialog)
    # Preview export
    # Pulsante "Export"
```

---

### 5.15 RF17 — Workflow Guidato (Stepper)

**Ispirato ai workflow multi-stage di LLM Wiki:**
1. Document Ingestion Pipeline (badge stati: not-ingested → queued → running → ingested)
2. Human-in-the-Loop Review (contradiction, duplicate, missing-page, confirm, suggestion)
3. Deep Research Pipeline (queued → searching → synthesizing → saving → done)
4. Agent Tool Execution (understanding → routing → tool_call → result → final)

**Fasi del Workflow OpenSpec:**

```
[1. Context]  →  [2. Propose]  →  [3. Review]  →  [4. Apply]  →  [5. Validate]
     ↑                                                                    │
     └────────────────────── (reject → back to propose) ──────────────────┘
```

| Step | Nome      | Descrizione                          | Azioni                             | Badge  |
| ---- | --------- | ------------------------------------ | ---------------------------------- | ------ |
| 1    | Context   | Raccolta contesto wiki + codebase    | wiki-query, codebase analyze       | 🔵     |
| 2    | Propose   | Generazione proposta OpenSpec        | openspec-propose, openspec-explore | 🟡     |
| 3    | Review    | Revisione e editing specifiche       | edit, validate, AI assist          | 🟠     |
| 4    | Apply     | Applicazione change                  | apply tasks, monitor progress      | 🔴     |
| 5    | Validate  | Validazione finale e sync specs      | validate, sync-specs, archive      | ✅     |

**Widget** (`stepper_widget.py`):
```python
class StepperWidget(QWidget):
    """Stepper orizzontale ispirato ai workflow di LLM Wiki.
    Stati: pending → active → complete → error."""

    step_changed = Signal(int)
    step_action_requested = Signal(int, str)

    # Rendering: cerchi numerati collegati da linee
    # Step attivo: accent color con animazione pulse (come LLM Wiki daemon dot)
    # Step futuri: disabilitati (non cliccabili, grayed out)
    # Step completati: check verde (come LLM Wiki success indicator)
    # Step errore: rosso con icona warning
```

---

## 6. Theming QSS — Dark Theme

**Palette derivata dall'analisi OKLCH di LLM Wiki** (§3.8), convertita in valori HEX
per compatibilità QSS:

**File:** `styles/dark-theme.qss`

| Variabile             | HEX       | Origine LLM Wiki                    | Uso                        |
| ---------------------- | --------- | ------------------------------------ | -------------------------- |
| `bg-primary`           | `#1a1b1e` | `oklch(0.16 0.005 260)`            | Sfondo principale          |
| `bg-card`              | `#25262b` | `oklch(0.205 0.005 260)`           | Card, pannelli elevati     |
| `bg-sidebar`           | `#141517` | Più scuro di bg-primary             | Sidebar rail               |
| `bg-input`             | `#2c2e33` | `oklch(0.269 0.005 260)`           | Input fields, muted bg     |
| `border`               | `#373a40` | `oklch(1 0 0 / 12%)`              | Bordi (white 12% opacity)  |
| `text-primary`         | `#f8f9fa` | `oklch(0.985 0 0)`                | Testo principale           |
| `text-secondary`       | `#909296` | `oklch(0.708 0 0)`                | Testo secondario/muted     |
| `accent`               | `#228be6` | Accent applicazione                  | Link, bottoni primari      |
| `accent-hover`         | `#339af0` | Accent hover                        | Hover stati                |
| `success`              | `#40c057` | Status indicator                     | CLI trovata, step ok       |
| `warning`              | `#fab005` | Warning indicator                    | Warnings, scanning         |
| `error`                | `#fa5252` | `oklch(0.704 0.191 22.216)`        | Errori, delete             |
| `bubble-user`          | `#228be6` | Primary blue                        | Sfondo bolla utente        |
| `bubble-user-text`     | `#ffffff` | White                               | Testo bolla utente         |
| `bubble-assistant`     | `#2c2e33` | Muted bg                            | Sfondo bolla assistente    |
| `bubble-assistant-text`| `#f8f9fa` | Foreground                          | Testo bolla assistente     |

**Font:** Come LLM Wiki usa Geist Variable (14px base). Per QSS: `"Segoe UI", "SF Pro", sans-serif` con font-size 14px base.

**Zoom:** Come LLM Wiki (`applyDocumentZoom`), implementare scaling via QApplication font size.

---

## 7. Layout UI — Adattamento a PySide6

### 7.1 Gerarchia Widget Finale (basata su analisi LLM Wiki)

```
QMainWindow (MainWindow)
├── QWidget (central_widget)
│   └── QHBoxLayout (main_layout)
│       │
│       ├── QWidget (icon_sidebar, fixed 48px)              ← icon-sidebar.tsx
│       │   └── QVBoxLayout
│       │       ├── QLabel (app_logo, 32x32)
│       │       ├── QPushButton × N (nav_buttons, icon-only, 40x40)
│       │       │   objectName: "nav_chat", "nav_wiki", "nav_sources", etc.
│       │       ├── QSpacerItem (stretch)
│       │       ├── StatusIndicator (daemon_status)          ← dot pulsante
│       │       ├── QPushButton (settings_btn)
│       │       └── QPushButton (switch_project_btn)
│       │
│       ├── QWidget (sidebar_panel, 150-400px, collapsible)  ← sidebar-panel.tsx
│       │   └── QVBoxLayout
│       │       ├── QTabWidget (sidebar_tabs)
│       │       │   ├── Tab "Knowledge" → KnowledgeTreeWidget (QTreeView)
│       │       │   └── Tab "Files" → FileTreeWidget (QTreeView)
│       │       └── ActivityPanel (bottom_drawer)            ← activity-panel.tsx
│       │           ├── QLabel (task_count + status)
│       │           ├── QProgressBar (current_task)
│       │           └── QListWidget (task_queue, collapsible)
│       │
│       ├── QWidget (content_area, stretch=1)                ← content-area.tsx
│       │   └── QVBoxLayout
│       │       ├── QWidget (toolbar_bar)
│       │       │   └── QHBoxLayout
│       │       │       ├── SearchBarView (QLineEdit, RF3)
│       │       │       ├── AgentSelectorView (QComboBox, RF10)
│       │       │       └── QPushButton (toolbar_actions)
│       │       ├── QStackedWidget (page_stack)
│       │       │   ├── WorkspaceView (index 0)       — Welcome/Info
│       │       │   ├── ChatView (index 1)             — RF4
│       │       │   ├── WikiBrowserView (index 2)      — RF5
│       │       │   ├── CodebaseView (index 3)         — RF7
│       │       │   ├── GraphView (index 4)            — RF8/RF9
│       │       │   ├── OpenSpecStepperView (index 5)  — RF17
│       │       │   ├── SearchView (index 6)           — RF3
│       │       │   ├── ReviewView (index 7)           — review
│       │       │   ├── CLIStatusView (index 8)        — RF11
│       │       │   └── SettingsView (index 9)
│       │       └── QWidget (status_bar)
│       │           └── QHBoxLayout
│       │               ├── StatusIndicator (cli_status)
│       │               ├── QLabel (workspace_path)
│       │               └── QLabel (agent_active)
│       │
│       └── QWidget (research_panel, collapsible, 250-50%)   ← research-panel.tsx
│           └── QVBoxLayout (context details, reference preview, outputs)
│
└── (no QMenuBar — sidebar-driven navigation, come LLM Wiki)
```

### 7.2 Regole di Visibilità (da LLM Wiki `app-layout-visibility.ts`)

```python
STANDALONE_VIEWS = {"chat", "settings", "cli_status"}
EMBEDDED_VIEWS = {"wiki", "sources", "search", "graph", "openspec", "review", "codebase"}

# Quando activeView in STANDALONE_VIEWS:
#   sidebar_panel.hide()
#   research_panel.hide()
#   content_area prende tutto lo spazio

# Quando activeView in EMBEDDED_VIEWS:
#   sidebar_panel.show()
#   research_panel disponibile (toggle)
```

### 7.3 View Routing (da LLM Wiki `wiki-store.ts`)

```python
# In MainWindow:
def _on_nav_clicked(self, view_id: str):
    """Cambia vista attiva nel QStackedWidget.
    Gestisce visibilità sidebar/research come LLM Wiki."""

    # Salva return view per navigazione indietro (come LLM Wiki previewReturnView)
    if view_id == "wiki" and self._current_view in ("search", "review"):
        self._return_view = self._current_view

    self._page_stack.setCurrentIndex(VIEW_INDEX_MAP[view_id])
    self._update_layout_visibility(view_id)
    self._current_view = view_id
```

---

## 8. Signal/Slot Wiring — Mappa Connessioni

### Workspace Flow
```
WorkspaceView.open_requested(path)
  → WorkspaceController.open_workspace(path)
    → WorkspaceModel.validate_workspace(path)
      → WorkspaceController.workspace_validated(result)
        → WorkspaceView._on_workspace_validated(result)
          → (se invalid) Dialog init → WorkspaceController.initialize_workspace(path)
            → WorkspaceController.workspace_initialized(path)
              → MainWindow._on_workspace_ready(path)
                → CLIController.start_scan()
                → WikiController.load_index()
                → MainWindow._switch_to_wiki_view()
```

### CLI Scan Flow
```
MainWindow._on_workspace_ready(path)
  → CLIController.start_scan()
    → CLIScanWorker.start() [QThread, login shell probe]
      → CLIScanWorker.cli_found(info) [per ogni CLI]
        → CLIController.cli_found(info)
          → CLIStatusView._on_cli_found(info)  [aggiorna card]
          → AgentSelectorView._on_cli_found(info)  [popola dropdown]
          → StatusIndicator._update_dot(info)  [sidebar dot]
      → CLIScanWorker.scan_complete(results)
        → CLIController.cli_scan_complete(results)
          → CLIStatusView._on_scan_complete(results)
          → AgentSelectorView._populate_all(results)
          → StatusBar._update_cli_count(results)
```

### Chat Flow (ispirato a LLM Wiki agent loop)
```
ChatInput.send_requested(text, context_files, skills)
  → ChatController.send_message(text, context_files, skills)
    → ChatModel.build_context(workspace, text)
    → ChatModel.format_prompt(messages, context)
    → ChatWorker.start() [QThread, subprocess CLI]
      → ChatWorker.tool_stage(stage_dict) [per ogni stage]
        → ChatController.tool_stage(stage_dict)
          → ChatBubble._add_tool_stage(stage_dict)
      → ChatWorker.token_received(token) [streaming]
        → ChatController.token_received(token)
          → ChatBubble._append_streaming(token)
      → ChatWorker.response_complete(message)
        → ChatController.message_received(message)
          → ChatView._add_message(message)
          → ContextPanel._update_references(message.sources)
```

---

## 9. Piano Iterativo di Sviluppo — Dettaglio Step-by-Step

> **Legenda:** ✅ = completato | ⬜ = da fare | 🔄 = in corso
>
> Ogni sub-step elenca i **file coinvolti** e le **dipendenze** da step precedenti.
> Aggiornare questa sezione man mano che il lavoro procede.

---

### Iterazione 1 — Foundation ✦

#### Step 1.0 — Scaffolding MVC + Shell UI (COMPLETATO)

Crea la struttura file/cartelle MVC, l'entry point, il tema QSS, e la shell
della finestra principale con sidebar, QStackedWidget placeholder, e status bar.

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.0.1 Struttura cartelle MVC | ✅ | `models/`, `views/`, `controllers/`, `workers/`, `utils/`, `tests/` | Cartelle + `__init__.py` con commenti di convenzione |
| 1.0.2 Costanti path SDD | ✅ | `utils/paths.py` | `REQUIRED_DIRS`, `REQUIRED_FILES`, template contents, `resolve()` |
| 1.0.3 Tema chiaro e scuro QSS | ✅ | `styles/dark-theme.qss`, `styles/light-theme.qss` | Temi chiaro e scuro basati su palette LLM Wiki, con switch dinamico basato su OS |
| 1.0.4 Entry point | ✅ | `main.py` | `QApplication`, font SF Pro 14px, QSS loading, `MainWindow` 1280×800 |
| 1.0.5 Icon Sidebar + Sidebar Panel | ✅ | `views/sidebar.py` | `IconSidebar` 48px rail + `SidebarPanel` collassabile con KnowledgeTree/FileTree tab |
| 1.0.6 Status Indicator | ✅ | `views/widgets/status_indicator.py` | Dot pulsante animato (ok/scanning/error/idle) via `QPainter` + `QPropertyAnimation` |
| 1.0.7 MainWindow shell | ✅ | `views/main_window.py` | Layout 4 zone, `QStackedWidget` con 13 placeholder, routing, regole visibilità standalone/embedded |
| 1.0.8 Workspace Model | ✅ | `models/workspace_model.py` | `validate_workspace()`, `initialize_workspace()`, `get_workspace_info()` — pure Python |
| 1.0.9 Workspace Controller | ✅ | `controllers/workspace_controller.py` | Mediatore MVC con signal `workspace_opened/validated/initialized/error`, recent projects via `QSettings` |
| 1.0.10 Workspace View | ✅ | `views/workspace_view.py` | Welcome Screen (logo, recent projects, Open button) + Info Panel (stats card, quick actions) |

**Stato complessivo Step 1.0:** ✅ Tutti i file creati. I componenti non sono ancora collegati tra loro.

---

#### Step 1.1 — Wiring Workspace (collegare ciò che esiste)

Collega Model → Controller → View nel `main.py` e inietta `WorkspaceView` nel
`MainWindow` tramite `replace_view()`. Dopo questo step l'app mostra la Welcome
Screen reale e permette di aprire/inizializzare un workspace.

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.1.1 Istanziare MVC in main.py | ✅ | `main.py` | Creare `WorkspaceModel` → `WorkspaceController(model)` → `WorkspaceView()`, passarli a `MainWindow` |
| 1.1.2 Iniettare WorkspaceView | ✅ | `main.py` | `window.replace_view("workspace", workspace_view)` |
| 1.1.3 Collegare signal/slot | ✅ | `main.py` | `workspace_view.open_requested → controller.open_workspace`, `controller.workspace_opened → main_window.set_workspace_path`, ecc. |
| 1.1.4 Popolare recent projects | ✅ | `main.py` | `controller.get_recent() → workspace_view.populate_recent()` all'avvio |
| 1.1.5 Gestire init workspace | ✅ | `main.py` | Se validazione fallisce → dialog "Inizializzare?" → `controller.initialize_workspace()` |

**Dipendenze:** Step 1.0 (tutto completato)
**Risultato:** L'app si avvia, mostra la Welcome Screen reale, puoi aprire un workspace e la status bar si aggiorna.

---

#### Step 1.2 — Shell Path Resolver + CLI Discovery Model

Crea la logica pura Python per trovare CLI AI nel sistema, incluso il fallback
login shell PATH probe per macOS (ispirato a `cli_resolver.rs` di LLM Wiki).

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.2.1 Shell Path Resolver | ✅ | `utils/shell_path_resolver.py` | `resolve_login_shell_path()` con `lru_cache`, timeout 10s, delimitatore `\x1e`, fallback. `find_cli_command()` con step shutil.which → candidati → login shell fallback |
| 1.2.2 CLI Registry e dataclass | ✅ | `models/cli_discovery_model.py` | `@dataclass CLIInfo(key, binary_name, display_name, found, path, version, cli_type)`. `CLI_REGISTRY` con 8 CLI: claude, codex, gemini, agy, aider, gh-copilot, ollama, continue |
| 1.2.3 Scan logic | ✅ | `models/cli_discovery_model.py` | `scan_all() → list[CLIInfo]`, `scan_single(key) → CLIInfo`, `get_version(path, flag, timeout=3)` |

**Dipendenze:** Nessuna (pure Python, zero Qt)
**Risultato:** `CLIDiscoveryModel().scan_all()` restituisce la lista di CLI trovate/non trovate con versioni.

---

#### Step 1.3 — CLI Scan Worker + Controller

Crea il QThread per eseguire la scansione CLI in background e il Controller
che espone i signal di progresso.

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.3.1 Base Worker | ✅ | `workers/base_worker.py` | `BaseWorker(QThread)` con pattern error handling + `finished` signal |
| 1.3.2 CLI Scan Worker | ✅ | `workers/cli_scan_worker.py` | `CLIScanWorker(QThread)` con signal `cli_found(CLIInfo)`, `scan_progress(int, int)`, `scan_complete(list)`, `scan_error(str)`. Itera `CLI_REGISTRY` in `run()` |
| 1.3.3 CLI Controller | ✅ | `controllers/cli_controller.py` | `CLIController(QObject)` con signal relay, `start_scan()` che lancia il worker, `get_available_agents() → list[CLIInfo]` |

**Dipendenze:** Step 1.2 (model + resolver)
**Risultato:** La scansione CLI avviene in background senza bloccare la UI, con signal di progresso.

---

#### Step 1.4 — CLI Status View

Crea la vista che mostra lo stato di ogni CLI AI con card e indicatori visivi.

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.4.1 CLI Status View | ✅ | `views/cli_status_view.py` | `CLIStatusView(QWidget)` con griglia di card per ogni CLI: icona + nome + `StatusIndicator` (verde = found, rosso = not found, ambra pulsante = scanning). Progress bar durante scansione. Pulsante "Rescan". Stili card spostati da inline a `styles/*.qss` (§10.5) |
| 1.4.2 Iniettare nel MainWindow | ✅ | `main.py` | `window.replace_view("cli_status", cli_status_view)` |

**Dipendenze:** Step 1.3 (controller con signal), Step 1.0.6 (StatusIndicator widget)
**Risultato:** Navigando su "CLI Status" nella sidebar si vedono le card con lo stato di ogni CLI.

---

#### Step 1.5 — Agent Model + Selector

Crea il model per la configurazione degli agenti e il dropdown nella toolbar.

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.5.1 Agent Model | ✅ | `models/agent_model.py` | `@dataclass AgentConfig(cli_key, display_name, model_name, extra_args, cli_type)`. `AgentModel` con `get_available_agents(found_clis)`, `set_active_agent()`, `get_active_agent()`. Bug corretto: il mapping modello default controllava `cli.key == "gpt"` (chiave inesistente nel registry) invece di `"codex"` |
| 1.5.2 Agent Selector View | ❌ | `views/agent_selector_view.py` | (Cancellato) Sostituito dal combo box `agent_combo` in `views/settings_view.py` (§8.2.1) |
| 1.5.3 Inserire nella toolbar | ❌ | `views/main_window.py` | (Cancellato) Rimosso per mantenere la UI pulita; selezione agente spostata in Settings |

**Dipendenze:** Step 1.3 (CLI scan results per sapere quali agenti sono disponibili)
**Risultato:** AgentModel gestisce l'agente attivo; la selezione manuale avviene da `SettingsView`, non da un selettore nella toolbar.

---

#### Step 1.6 — Wiring Finale Iterazione 1

Collega tutti i componenti dell'Iterazione 1 in `main.py` per il flusso end-to-end.

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 1.6.1 Auto-scan CLI dopo apertura workspace | ✅ | `main.py` | `controller.workspace_opened → cli_controller.start_scan()`; inoltre lo scan parte già all'avvio app (non solo dopo apertura workspace) |
| 1.6.2 Aggiornare status bar | ✅ | `main.py` | `cli_controller.cli_scan_complete → main_window.set_cli_count()` |
| 1.6.3 Popolare agent selector | ❌ | `main.py` | (Cancellato) Non abbiamo più il selettore in toolbar; il combo box è in `SettingsView` (auto-popolato al termine dello scan) |
| 1.6.4 Status indicator sidebar | ❌ | `main.py` | (Cancellato) Pallino indicatore rimosso dalla sidebar |
| 1.6.5 Agente attivo in status bar | ✅ | `main.py` | Al termine dello scan l'agente preferito (da `QSettings`) o il primo disponibile viene selezionato automaticamente; la scelta manuale in `SettingsView` aggiorna `set_active_agent()` via il segnale `agent_changed` |
| 1.6.6 Test manuale end-to-end | ✅ | — | Avvio app verificato headless (`QT_QPA_PLATFORM=offscreen`): nessuna eccezione, wiring workspace/CLI/wiki/chat/import confermato per lettura codice |

**Dipendenze:** Tutti gli step 1.1–1.5
**Risultato:** Iterazione 1 completa e verificata. L'app è funzionante con Welcome Screen, workspace management, CLI discovery, selezione agente da Settings, e navigazione. Due violazioni MVC (§10.1) corrette: `utils/config.py` importava `QSettings` (rimosso, logica spostata in `ChatController`); `WikiController.start_import()` importava `QMessageBox` e manipolava `ActivityPanel` direttamente (ora emette segnali `import_started/import_progress/import_complete`, gestiti dal wiring in `main.py`).

---

### Iterazione 2 — Knowledge Base

#### Step 2.1 — Wiki Model + Index Parser

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 2.1.1 Wiki Model | ✅ | `models/wiki_model.py` | `WikiModel` con `import_document(workspace, source)`, `parse_index()`, `list_pages()`, `read_page()`, `get_page_frontmatter()`. `SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt", ".rst", ".docx"]` (firma `import_document` invertita rispetto alla bozza originale, ma coerente in tutto il codebase) |
| 2.1.2 Markdown parser utility | ✅ | `utils/markdown_parser.py` | Parser `index.md` → `ParsedIndex` (frontmatter + categorie di `WikiLink`). Parsing YAML frontmatter con fallback line-by-line |
| 2.1.3 File utilities | ✅ | `utils/file_utils.py` | `safe_write()`, `backup_file()`, `atomic_copy()` — tutte con scrittura atomica via file temporaneo + `os.replace()` |

**Dipendenze:** Step 1.1 (workspace aperto con path valido)

---

#### Step 2.2 — Wiki Browser View

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 2.2.1 Knowledge Tree Widget | ✅ | `views/wiki_browser_view.py` | `KnowledgeTreeModel(QStandardItemModel)` popola il `QTreeView` della sidebar raggruppato per categoria di `index.md`, con icone Lucide per categoria |
| 2.2.2 Page Reader Panel | ✅ | `views/wiki_browser_view.py` | `QTextBrowser` con rendering Markdown → HTML (estensioni `fenced_code`, `tables`), toolbar Back/Forward/Refresh basata sulla history nativa di `QTextBrowser` |
| 2.2.3 Wiki Controller | ✅ | `controllers/wiki_controller.py` | Mediatore MVC con signal `index_loaded`, `page_selected`, `page_loaded`, `error_occurred` + segnali import (§2.3.5) |
| 2.2.4 Wiring + inject | ✅ | `main.py` | `replace_view("wiki", wiki_browser_view)`, `QTreeView` della sidebar passato al costruttore della view |

**Dipendenze:** Step 2.1

---

#### Step 2.3 — Import Documenti + Activity Panel

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 2.3.1 File Drop Area widget | ✅ | `views/widgets/file_drop_area.py` | `QLabel` con drag-and-drop, feedback visivo via proprietà QSS dinamica `drag_active` (`style().unpolish/polish`) |
| 2.3.2 Wiki Import View | ✅ | `views/wiki_import_view.py` | `QDialog` con `FileDropArea` + Browse, lista file (`QListWidget`), pulsante "Import All". Stato per-file (not-ingested→ingested) non tracciato nel dialog: il progresso viene mostrato a livello di task nell'Activity Panel dopo l'emit di `import_requested` |
| 2.3.3 Import Worker | ✅ | `workers/import_worker.py` | `ImportWorker(BaseWorker)` — copia file in `knowledge-base/raw/` via `atomic_copy`, signal `import_progress(int,int,str)`, `import_complete(list)` |
| 2.3.4 Activity Panel | ✅ | `views/widgets/activity_panel.py` | Bottom drawer nella sidebar: `start_task`/`update_task`/`complete_task`, empty state, stili spostati in QSS |
| 2.3.5 Wiring import | ✅ | `main.py` | Quick action "Import Docs" → apre dialog (bloccato con avviso se nessun workspace aperto) → `WikiController.start_import()` emette segnali → wiring in `main.py` li collega ad `ActivityPanel` e a `QMessageBox` di conferma (§10.1: il controller non tocca widget direttamente) |

**Dipendenze:** Step 2.1, Step 2.2
**Risultato:** Iterazione 2 completa e verificata. Stili inline rimossi da `wiki_import_view.py` e `activity_panel.py` (§10.5).

---

### Iterazione 3 — Chat LLM

#### Step 3.1 — Chat Model + Persistenza

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 3.1.1 Chat Message dataclass | ✅ | `models/chat_model.py` | `@dataclass ChatMessage(role, content, timestamp, sources, tool_events)` con `to_dict()`/`from_dict()` per la persistenza JSON |
| 3.1.2 Chat Model | ✅ | `models/chat_model.py` | `save_conversation()`, `load_conversation()`, `list_conversations()`, `build_context()` (legge `index.md` via `WikiModel`). `format_prompt()`/`parse_response()` non implementati: il worker (3.3.2) costruisce/parsifica autonomamente |
| 3.1.3 Config utility | ❌ | — | **Rimosso** (§10.1): un `utils/config.py` che avvolge `QSettings` violerebbe "utils/ → ZERO import da PySide6". Ogni controller che necessita di `QSettings` lo istanzia direttamente (pattern già usato da `WorkspaceController`, esteso a `ChatController`) |

**Dipendenze:** Step 2.1 (wiki model per context building)

---

#### Step 3.2 — Chat Widgets

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 3.2.1 Chat Bubble widget | ✅ | `views/widgets/chat_bubble.py` | Bolle user (right, accent bg) / assistant (left, muted bg) via proprietà QSS `bubble_role`. Markdown rendering (`QTextBrowser.setMarkdown`). Citations pill non implementate (nessuna sorgente da citare finché il worker è simulato, vedi 3.3.2) |
| 3.2.2 Chat Input widget | ✅ | `views/widgets/chat_input.py` | `QTextEdit` (max 100px), toolbar con Attach + Send. Web toggle / Mode ▼ / chip attivi non implementati (nice-to-have non ancora richiesti) |
| 3.2.3 Conversation Sidebar widget | ✅ | `views/widgets/conversation_sidebar.py` | Lista conversazioni (titolo, count messaggi in tooltip), "+ New Chat". Hover-delete non implementato |
| 3.2.4 Tool Stage widget | ✅ | `views/widgets/tool_stage_widget.py` | Accordion collapsabile singolo stage (nome + dettaglio), toggle via proprietà QSS `expanded`. Non modella la sequenza a 4 fasi understanding→routing→tool_call→result della spec: ogni stage è indipendente |

**Dipendenze:** Nessuna (widget puri)
**Nota:** Tutti gli stili inline (`setStyleSheet`) di questi 4 widget sono stati spostati in `styles/dark-theme.qss` / `light-theme.qss` (§10.5).

---

#### Step 3.3 — Chat View + Worker + Controller

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 3.3.1 Chat View | ✅ | `views/chat_view.py` | Layout: `ConversationSidebar` (240px fisso) + messages scroll + context panel (300px, nascosto finché non popolato). Compone `ChatBubble`, `ChatInput`, `ToolStageWidget` |
| 3.3.2 Chat Worker | ✅ | `workers/chat_worker.py` | **Reale**: estende `BaseWorker` (non più `QThread` diretto), spawna `subprocess.Popen([binary_path, *args], cwd=workspace_path)` e stream-a `stdout` riga per riga. Costruzione argv e parsing per-CLI in `models/chat_model.py` (`build_cli_args`, `get_stream_format`, `parse_claude_json_line`). Solo `claude` ha parsing strutturato (`--output-format stream-json` → eventi `text`/`tool_use`/`result`); le altre 7 CLI del registry (§5.2) stream-ano testo grezzo riga per riga. `response_error` è un alias del segnale `error` ereditato da `BaseWorker` |
| 3.3.3 Chat Controller | ✅ | `controllers/chat_controller.py` | Mediatore: `send_message()`, relay signal worker → view, persistenza conversazione via `ChatModel`. `set_active_cli(cli_key, binary_path)` riceve la CLI attiva dal wiring in `main.py` (mai risolta da solo, §10.1); blocca l'invio con `stream_error` se nessuna CLI è disponibile. `set_wiki_model()` inietta il `WikiModel` per `build_context()` (era `None` a placeholder, ora reale) |
| 3.3.4 Wiring chat | ✅ | `main.py` | `replace_view("chat", chat_view)`, wiring in `_wire_chat()` (streaming token→bubble, tool stage→widget, errori). `settings_view.agent_changed` e `_handle_cli_scan_complete()` risolvono il path binario dalla scansione CLI e chiamano `chat_controller.set_active_cli()` |

**Dipendenze:** Step 3.1, Step 3.2, Step 1.3 (cli_controller per sapere quale CLI usare)
**Nota:** l'invocazione reale copre tutte le 8 CLI del registry con argv "best-effort" (flag non verificati per ognuna — potrebbero necessitare aggiustamenti per la versione installata di ciascun tool), ma solo `claude` ha un parser di streaming strutturato documentato. La cronologia dei messaggi precedenti non viene ancora iniettata nel prompt (ogni invocazione è "stateless": solo contesto wiki + ultimo messaggio) — possibile miglioramento futuro con sessioni CLI persistenti (es. `claude --continue`).

---

### Iterazione 4 — Analisi Codebase

#### Step 4.1 — Codebase Analysis

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 4.1.1 Codebase Model | ⬜ | `models/codebase_model.py` | `analyze_structure()`, `detect_languages()`, `generate_report()` |
| 4.1.2 Codebase Worker | ⬜ | `workers/codebase_worker.py` | `QThread` per analisi in background con progress |
| 4.1.3 Codebase View | ⬜ | `views/codebase_view.py` | `QSplitter` con file tree (`QTreeView`) + report panel (stats cards + `QTextBrowser` markdown) |
| 4.1.4 Codebase Controller | ⬜ | `controllers/codebase_controller.py` | Mediatore con signal `analysis_started/complete/error` |
| 4.1.5 Wiring codebase | ⬜ | `main.py` | `replace_view("codebase", codebase_view)`, quick action "Analyze Codebase" |

**Dipendenze:** Step 1.1 (workspace path)

---

### Iterazione 5 — Grafo

#### Step 5.1 — Graph Visualization

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 5.1.1 Graph Model | ⬜ | `models/graph_model.py` | `load_graph()`, `graph_exists()`, `get_node_details()`, `generate_html_visualization()` (Sigma.js + Graphology + ForceAtlas2 + Louvain) |
| 5.1.2 Graph View | ⬜ | `views/graph_view.py` | Toolbar (layout selector, node search, community filter) + `QWebEngineView` + details panel collassabile. Fallback "Graph data not found" |
| 5.1.3 Graph Controller | ⬜ | `controllers/graph_controller.py` | Mediatore con signal `graph_loaded`, `node_selected` |
| 5.1.4 Wiring grafo | ⬜ | `main.py` | `replace_view("graph", graph_view)`, caricamento graph.json dopo workspace open |

**Dipendenze:** Step 1.1 (workspace path), PySide6-WebEngine

---

### Iterazione 6 — OpenSpec Core

#### Step 6.1 — OpenSpec Model

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 6.1.1 OpenSpec Model | ⬜ | `models/openspec_model.py` | `list_changes()`, `list_specs()`, `read_artifact()`, `create_change()`, `build_cli_command()`, `parse_cli_output()`, `validate_change()`, `validate_spec()` |
| 6.1.2 OpenSpec Worker | ⬜ | `workers/openspec_worker.py` | `QThread` per generazione specs via CLI AI in background |

**Dipendenze:** Step 1.2 (CLI resolver per trovare il binario AI)

---

#### Step 6.2 — OpenSpec Editor + Stepper

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 6.2.1 Stepper Widget | ⬜ | `views/widgets/stepper_widget.py` | Stepper orizzontale: cerchi numerati (pending → active → complete → error) con linee connettive. Signal `step_changed`, `step_action_requested` |
| 6.2.2 OpenSpec Editor View | ⬜ | `views/openspec_editor_view.py` | `QSplitter` split: editor panel (tab + `QTextEdit` syntax highlighted + toolbar save/validate/export/history) + assistant panel (mini ChatView) |
| 6.2.3 OpenSpec Stepper View | ⬜ | `views/openspec_stepper_view.py` | Workflow 5 fasi: Context → Propose → Review → Apply → Validate. Usa `StepperWidget` + pannello azioni per fase |
| 6.2.4 OpenSpec Controller | ⬜ | `controllers/openspec_controller.py` | Mediatore lifecycle OpenSpec con signal per ogni transizione di stato |
| 6.2.5 Wiring OpenSpec | ⬜ | `main.py` | `replace_view("openspec", openspec_stepper_view)`, collegare CLI + wiki context |

**Dipendenze:** Step 6.1, Step 3.2 (ChatBubble/ChatInput per mini assistant)

---

### Iterazione 7 — OpenSpec Advanced

#### Step 7.1 — Validazione + History + Export

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 7.1.1 Validation Worker | ⬜ | `workers/validation_worker.py` | `QThread` per validazione coerenza in background |
| 7.1.2 OpenSpec History View | ⬜ | `views/openspec_history_view.py` | Lista revisioni con timestamp + diff viewer colorato + restore button |
| 7.1.3 OpenSpec Export View | ⬜ | `views/openspec_export_view.py` | `QDialog` con selezione formato (JSON/MD/YAML), checklist specs, directory output, preview |
| 7.1.4 Wiring validazione/history/export | ⬜ | `views/openspec_editor_view.py` | Toolbar buttons → dialoghi/pannelli corrispondenti |

**Dipendenze:** Step 6.2

---

### Iterazione 8 — Polish

#### Step 8.1 — Ricerca + Review

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 8.1.1 Search Model | ⬜ | `models/search_model.py` | `build_index()`, `search()` full-text su wiki + specs |
| 8.1.2 Search Bar View | ⬜ | `views/search_bar_view.py` | `QLineEdit` nella toolbar con popup risultati live. Signal `search_requested`, `result_selected` |
| 8.1.3 Search Controller | ⬜ | `controllers/search_controller.py` | Mediatore ricerca |
| 8.1.4 Review View | ⬜ | `views/review_view.py` | Coda review human-in-the-loop (contradiction, duplicate, missing-page, confirm, suggestion) |

**Dipendenze:** Step 2.1 (wiki model per indicizzazione)

---

#### Step 8.2 — Settings + Shortcuts + Testing

| Sub-step | Stato | File | Descrizione |
|----------|-------|------|-------------|
| 8.2.1 Settings View | ⬜ | `views/settings_view.py` | Vista tabbed per configurazione (LLM, tema, workspace, ecc.) |
| 8.2.2 Keyboard shortcuts | ⬜ | `views/main_window.py` | `Cmd+,` per settings, `Cmd+K` per search, ecc. |
| 8.2.3 Error handling globale | ⬜ | `main.py`, `workers/base_worker.py` | Exception handler globale, error dialog, logging |
| 8.2.4 Persistenza stato | ⬜ | `utils/config.py` | `QSettings` per geometria finestra, ultima vista, preferenze utente |
| 8.2.5 Light theme | ✅ | `styles/light-theme.qss` | Tema chiaro basato su palette LLM Wiki light (§3.8) |
| 8.2.6 Test suite | ⬜ | `tests/test_workspace_model.py`, `tests/test_cli_discovery.py`, `tests/test_shell_path_resolver.py`, `tests/test_wiki_model.py`, `tests/test_openspec_model.py` | pytest + pytest-qt per model e controller |

**Dipendenze:** Tutti gli step precedenti

---

### Riepilogo Avanzamento

| Iterazione | Step | Stato | Descrizione |
|------------|------|-------|-------------|
| 1 Foundation | 1.0 Scaffolding | ✅ | Struttura MVC, tema, shell UI |
| 1 Foundation | 1.1 Wiring Workspace | ✅ | Collegare Welcome Screen |
| 1 Foundation | 1.2 CLI Discovery | ✅ | Shell path resolver + CLI model |
| 1 Foundation | 1.3 CLI Worker | ✅ | QThread scan + controller |
| 1 Foundation | 1.4 CLI Status View | ✅ | Vista card CLI |
| 1 Foundation | 1.5 Agent Selector | ✅ | Model agenti + selezione da Settings |
| 1 Foundation | 1.6 Wiring Finale | ✅ | Tutto collegato end-to-end (verificato con avvio headless) |
| 2 Knowledge Base | 2.1 Wiki Model | ✅ | Model + parser |
| 2 Knowledge Base | 2.2 Wiki Browser | ✅ | Tree + reader |
| 2 Knowledge Base | 2.3 Import + Activity | ✅ | Drag-drop + queue |
| 3 Chat LLM | 3.1 Chat Model | ✅ | Dataclass + persistenza |
| 3 Chat LLM | 3.2 Chat Widgets | ✅ | Bubble, input, sidebar |
| 3 Chat LLM | 3.3 Chat View | ✅ | View/Controller/Wiring + Worker con invocazione CLI reale via subprocess |
| 4 Codebase | 4.1 Analysis | ⬜ | Model + view + worker |
| 5 Grafo | 5.1 Graph | ⬜ | Sigma.js + QWebEngine |
| 6 OpenSpec Core | 6.1 Model | ⬜ | Model + worker |
| 6 OpenSpec Core | 6.2 Editor + Stepper | ⬜ | UI workflow 5 fasi |
| 7 OpenSpec Adv. | 7.1 Validation/History | ⬜ | Validazione + versioning + export |
| 8 Polish | 8.1 Search + Review | ⬜ | Ricerca + human-in-the-loop |
| 8 Polish | 8.2 Settings + Test | ⬜ | Config + shortcuts + testing |

---

## 10. Regole Tassative di Sviluppo

> Derivate da `pyqt6-ui-development-rules` adattate a PySide6.

### 10.1 MVC Separation
```
models/     → ZERO import da PySide6. Solo logica pura Python.
controllers/ → Import PySide6.QtCore (QObject, Signal). MAI widget.
views/       → Import PySide6.QtWidgets. MAI logica di business.
workers/     → Import PySide6.QtCore (QThread, Signal). Task I/O bound.
utils/       → ZERO import da PySide6. Utility pure Python.
```

### 10.2 Signal/Slot
```python
# ✅ CORRETTO — View emette signal, Controller gestisce
class MyView(QWidget):
    action_requested = Signal(str)

    def __init__(self, controller):
        self._btn.clicked.connect(lambda: self.action_requested.emit(self._input.text()))
        controller.result_ready.connect(self._on_result)

# ❌ VIETATO — View chiama direttamente il Model
class MyView(QWidget):
    def __init__(self, model):
        self._btn.clicked.connect(lambda: model.do_stuff(self._input.text()))
```

### 10.3 Threading
```python
# ✅ CORRETTO — I/O in QThread (login shell probe può richiedere 10s!)
class CLIScanWorker(QThread):
    result = Signal(object)
    def run(self):
        data = model.scan_all()  # include login shell PATH probe
        self.result.emit(data)

# ❌ VIETATO — I/O sul main thread
class CLIStatusView(QWidget):
    def on_scan_click(self):
        data = model.scan_all()  # BLOCCA LA UI PER 10+ SECONDI
```

### 10.4 Layout
```python
# ✅ CORRETTO — Layout manager, stretch, dimensioni relative
layout = QVBoxLayout()
layout.addWidget(widget, stretch=1)
sidebar.setFixedWidth(48)  # come LLM Wiki icon rail

# ❌ VIETATO
widget.setGeometry(10, 20, 300, 400)
widget.move(100, 200)
```

### 10.5 Theming
```python
# ✅ CORRETTO — QSS a livello QApplication, object names per targeting
app.setStyleSheet(Path("styles/dark-theme.qss").read_text())
widget.setObjectName("icon_sidebar")  # referenziabile in QSS

# ❌ VIETATO — stili inline
widget.setStyleSheet("background: red; color: white;")
```

---

## 11. Dipendenze Python

```toml
# pyproject.toml
[project]
name = "sdd-orchestrator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.6",
    "PySide6-WebEngine>=6.6",         # RF8/RF9 grafo (opzionale)
    "pyyaml>=6.0",                     # parsing config OpenSpec
    "python-frontmatter>=1.0",         # parsing frontmatter MD (come LLM Wiki)
    "markdown>=3.5",                   # rendering MD → HTML
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-qt>=4.3",
    "ruff>=0.4",
]
```

---

## 12. Entry Point

```python
# main.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SDD Orchestrator")
    app.setOrganizationName("SDD")

    # Font base 14px (come LLM Wiki Geist 14px)
    font = QFont("SF Pro", 14)  # Fallback: "Segoe UI" su Windows
    app.setFont(font)

    # Caricamento QSS globale (palette da LLM Wiki OKLCH analysis)
    qss_path = Path(__file__).parent / "styles" / "dark-theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text())

    window = MainWindow()
    window.setWindowTitle("SDD Orchestrator")
    window.resize(1280, 800)  # Dimensione iniziale ragionevole
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## Appendice A — Comandi Tauri di LLM Wiki (Riferimento)

LLM Wiki registra **74 comandi Tauri**. I più rilevanti per SDD Orchestrator:

| Categoria           | Comandi Chiave                                             | Equivalente SDD                    |
| ------------------- | ---------------------------------------------------------- | ---------------------------------- |
| CLI Detection       | `claude_cli_detect`, `codex_cli_detect`                   | `CLIDiscoveryModel.scan_single()`  |
| CLI Execution       | `claude_cli_spawn`, `codex_cli_spawn`, `*_kill`           | `ChatWorker` subprocess            |
| Project             | `create_project`, `open_project`                          | `WorkspaceModel.initialize/open()` |
| File I/O            | `read_file`, `write_file`, `list_directory`, `preprocess_file` | `file_utils.py`              |
| Search              | `search_project` (RRF: lexical + vector + graph)          | `SearchModel.search()`             |
| File History        | `list_file_history`, `restore_file_history`               | `OpenSpecModel.get_change_history()`|
| Agent               | `agent_start_turn`, `agent_cancel_turn`, `agent_list_sessions` | `ChatController` + `ChatWorker` |
| Skills              | `agent_list_skills`                                       | Discovery `.agents/skills/`        |

## Appendice B — Struttura LLM Wiki Workspace (Riferimento Completo)

```
<project_root>/
├── raw/sources/               → knowledge-base/raw/ in SDD
├── raw/assets/                → knowledge-base/raw/assets/ in SDD
├── wiki/entities/             → knowledge-base/pages/entities/ in SDD
├── wiki/concepts/             → knowledge-base/pages/concepts/ in SDD
├── wiki/sources/              → knowledge-base/pages/sources/ in SDD
├── wiki/queries/              → knowledge-base/pages/questions/ in SDD
├── wiki/comparisons/          → (non mappato direttamente)
├── wiki/synthesis/            → (non mappato direttamente)
├── wiki/index.md              → knowledge-base/index.md in SDD
├── wiki/log.md                → knowledge-base/log.md in SDD
├── schema.md                  → AGENTS.md in SDD
├── purpose.md                 → (nel contesto OpenSpec)
├── agent-workspace/           → (output generati, .agents/ in SDD)
├── .obsidian/                 → (non applicabile)
└── .llm-wiki/                 → .sdd/ (metadata interni) in SDD
    ├── project.json
    ├── lancedb/
    ├── agent-sessions/
    ├── skills/
    └── file-history/
```
