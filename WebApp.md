# LAIOS Web App

A React-based web interface for interacting with LAIOS through your browser.

## Prerequisites

- **Python 3.10+** with LAIOS installed
- **Node.js 18+** (only needed if you want to modify the frontend)
- **API dependencies** installed:
  ```sh
  python -m pip install -e ".[api]"
  ```

## Running the Web App

From the LAIOS project root:

```sh
python -m laios.ui.cli serve --port 8000
```
**pro-tip: make sure that your in the laios/LAIOS dir Otherwise it will not work**


Then open **http://localhost:8000** in your browser.
The server hosts both the API and the web UI on the same port.

## Pages

| Page | Description |
|------|-------------|
| **Dashboard** | System health overview, LLM status, tool/plugin counts |
| **Chat** | Real-time chat with the agent via WebSocket |
| **Sessions** | Create, view, and delete sessions |
| **Tools** | Browse all 16 built-in tools, view parameters, execute directly |
| **Plugins** | View loaded plugins, enable or disable them |
| **Health** | Detailed health checks with auto-refresh every 10 seconds |

## Rebuilding the Frontend

If you modify files in `web/src/`, rebuild the production bundle:

```sh
cd web
npm install
npm run build
```

Then restart the server. The new build is served automatically.

## Development Mode

For live-reloading while developing the frontend, run two terminals:

```sh
# Terminal 1 - Backend
python -m laios.ui.cli serve --port 8000

# Terminal 2 - Vite dev server with hot reload
cd web
npm run dev
```

Visit **http://localhost:5173** during development. Vite proxies all `/api` and `/ws` requests to the backend on port 8000.

## Troubleshooting

**"uvicorn not installed"** - Run `python -m pip install -e ".[api]"`

**Port already in use** - Another process is using port 8000. Either stop it or use a different port: `python -m laios.ui.cli serve --port 3000`

**pip not working** - If `pip install` fails with a path error, use `python -m pip install` instead.
