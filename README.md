# NL 3D Modeler

Generate 3D CAD models from natural language using an LLM and CADQuery.

## Architecture

### Backend (Python + FastAPI)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/chat` | POST | Send NL message, receive CADQuery code + OBJ model data |
| `/api/model` | GET | Fetch current OBJ data for 3D viewer |
| `/api/export?format=stl\|step` | POST | Export current model as STL or STEP |
| `/api/settings` | GET/PUT | Manage API endpoint, model name, API key |

**Processing Pipeline:**
1. User sends NL message in chat
2. Backend builds prompt: system instructions + full conversation history + current CADQuery script state
3. LLM (via llama-server OpenAI-compatible API) returns cumulative CADQuery script
4. Backend executes script in a restricted namespace
5. On success: exports to OBJ for viewer, updates state
6. On failure: auto-retries once by sending error back to LLM; if still failing, shows error to user

**Visual Feedback Loop:**
1. After CADQuery script executes and OBJ is generated, backend launches a headless browser via Playwright
2. The headless browser loads a minimal Three.js renderer, loads the OBJ, and captures a screenshot
3. Screenshot is sent to the LLM as vision context so the model can self-assess its output
4. If the LLM determines the result looks wrong, it auto-generates a corrected script (repeat up to N times)
5. Final validated code + OBJ sent to frontend

### Frontend (Plain HTML/CSS/JS + Three.js)

Three-panel layout:
- **Chat pane** — NL input and model responses
- **Code pane** — syntax-highlighted CADQuery script output
- **3D viewer pane** — interactive Three.js rendering of OBJ model with OrbitControls

Features:
- Settings modal for API endpoint URL, model name, optional API key
- Export dropdown to download STL or STEP files
- Session-only state (in-memory, no persistence)

### Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| 3D modeling | CADQuery (Open Cascade Python) |
| LLM client | OpenAI-compatible API client (vision-capable) |
| Frontend 3D | Three.js + OrbitControls |
| OBJ parsing | Three.js OBJLoader |
| Screenshot | Playwright headless browser |
| Containerization | Docker Compose |

### Project Structure

```
modeler/
  backend/
    main.py              # FastAPI app, routes, state management
    llm_client.py        # OpenAI-compatible API client (vision + text)
    executor.py          # CADQuery script executor with error handling
    exporter.py          # OBJ/STL/STEP export utilities
    screenshot.py        # Playwright headless Three.js screenshot capture
  frontend/
    index.html           # 3-panel layout
    css/style.css        # Layout and styling
    js/app.js            # Chat, settings, export logic
    js/viewer.js         # Three.js 3D viewer
  docker-compose.yml
  Dockerfile
  requirements.txt
```

### Docker

Single-service `docker-compose.yml`:
- Python image with CADQuery/OCP, Playwright dependencies
- FastAPI running with uvicorn
- Frontend served as static files from FastAPI
- Default llama-server endpoint configurable via env vars or settings UI

### Build Order

1. **Backend foundation** — `main.py`, `llm_client.py`, `executor.py`, `exporter.py`, `screenshot.py`, `requirements.txt`
2. **Frontend** — `index.html`, `style.css`, `app.js`, `viewer.js`
3. **Docker** — `Dockerfile`, `docker-compose.yml`

### Key Design Decisions

- Cumulative/stateful script — each message builds on prior CADQuery context
- Three.js + OBJ for 3D viewer, OrbitControls for interactive rotation
- Auto-retry once on LLM code errors, then surface error to user
- Vision-based self-assessment: headless Playwright captures screenshot, LLM sees what it built
- Session-only state (in-memory, no persistence across restarts)
