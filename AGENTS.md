# MIROFISH — SWARM-INTELLIGENCE SIMULATION ENGINE

## OVERVIEW

MiroFish is a swarm-intelligence simulation and prediction engine that models collective behavior across social platforms. Built with a Python Flask backend and Vue 3 frontend, it uses CAMEL-AI's OASIS framework to simulate multi-agent interactions on Reddit and Twitter, enabling prediction and analysis of emergent group dynamics. The system combines LLM-powered agents with memory persistence (Zep Cloud) to create realistic social simulations.

## STRUCTURE

mirofish/
├── backend/
│   ├── app/
│   ├── logs/
│   ├── scripts/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
├── static/
│   └── image/
├── AGENTS.md
├── README.md
├── package.json

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Flask API entry point | `backend/run.py` | Port 5001, UTF-8 console handling |
| REST endpoints | `backend/app/api/` | Flask routes and handlers |
| Business logic | `backend/app/services/` | Core simulation services |
| Data models | `backend/app/models/` | Pydantic models |
| Configuration | `backend/app/config.py` | Environment-based config |
| Reddit simulation | `backend/scripts/run_reddit_simulation.py` | CAMEL-AI OASIS Reddit agents |
| Twitter simulation | `backend/scripts/run_twitter_simulation.py` | CAMEL-AI OASIS Twitter agents |
| Parallel simulations | `backend/scripts/run_parallel_simulation.py` | Multi-platform orchestration |
| Event logging | `backend/scripts/action_logger.py` | Simulation action tracking |
| Vue app entry | `frontend/src/main.js` | Vue 3 + Router setup |
| UI components | `frontend/src/components/` | Reusable Vue components |
| Page views | `frontend/src/views/` | Top-level page components |
| Visualization | Frontend (D3 7.9.0) | Network graphs, swarm dynamics |
| Docker setup | `docker-compose.yml` | Ports 3000 (frontend), 5001 (backend) |

## COMMANDS

```bash
pnpm backend                           # cd backend && uv run python run.py
pnpm build                           # cd frontend && npm run build
pnpm dev                           # concurrently --kill-others -n "backend,frontend" -c "green,cyan" "npm run backend" "npm run frontend"
pnpm frontend                           # cd frontend && npm run dev
pnpm setup                           # npm install && cd frontend && npm install
pnpm setup:all                           # npm run setup && npm run setup:backend
pnpm setup:backend                           # cd backend && uv sync
```

## CONVENTIONS

**Python (Backend)**:
- Python 3.11+ required
- Package manager: `uv` (fast pip replacement)
- Dependencies: Flask 3.0+, OpenAI SDK, CAMEL-AI 0.2.78, Zep Cloud 3.13.0
- Entry point: `backend/run.py` (Flask app factory pattern)
- Config: Environment variables via `.env` (validated on startup)
- Encoding: UTF-8 console handling for Windows compatibility
- File uploads: `backend/uploads/` directory
- Simulation scripts: Standalone executables in `backend/scripts/`

**TypeScript/JavaScript (Frontend)**:
- Vue 3.5.24 with Composition API
- Build tool: Vite 7.2.4
- Routing: Vue Router 4.6.3
- HTTP client: Axios 1.13.2
- Visualization: D3 7.9.0 for network graphs
- Dev server: `--host` flag for network access

**Monorepo**:
- Root `package.json` orchestrates both stacks via npm scripts
- `concurrently` runs backend + frontend in parallel during dev
- Frontend proxies API requests to backend (port 5001)

**Docker**:
- Image: `ghcr.io/666ghj/mirofish:latest`
- Ports: 3000 (frontend), 5001 (backend)
- Volume: `./backend/uploads` mounted for persistence
- Environment: `.env` file required

## ANTI-PATTERNS

| Forbidden | Why |
|-----------|-----|
| Hardcoded API keys in source | Use `.env` for OpenAI, Zep Cloud credentials |
| Running backend without config validation | `Config.validate()` must pass before Flask starts |
| Mixing sync/async in Flask routes | Flask 3.0 supports async routes; use consistently |
| Committing `backend/uploads/` content | User data, should be gitignored |
| Skipping UTF-8 encoding setup on Windows | Console output will break with Chinese content |
| Installing deps without `uv` | Backend uses `uv sync`, not `pip install` |
| Hardcoded ports in frontend | Use Vite proxy config for API base URL |
| Running simulations without memory backend | Zep Cloud required for agent memory persistence |
| Blocking I/O in simulation scripts | Use async patterns for LLM calls |
| Missing error handling in API routes | All endpoints must handle validation + service errors |

## NOTES

- **Test coverage**: Minimal (1 placeholder test file); production readiness requires test expansion
- **Memory backend**: Zep Cloud 3.13.0 provides persistent agent memory across simulations
- **CAMEL-AI**: OASIS 0.2.5 framework powers social platform agent simulations
- **Encoding**: Windows console UTF-8 handling in `run.py` prevents Chinese character corruption
- **File processing**: PyMuPDF for PDFs, charset-normalizer for non-UTF-8 text files
- **Monorepo pattern**: Root npm scripts delegate to backend (uv) and frontend (npm) package managers
- **Docker image**: Pre-built image available; rebuild via `Dockerfile` if customizing
- **License**: AGPL-3.0
