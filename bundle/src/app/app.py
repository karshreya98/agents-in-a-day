"""Marc's Maintenance Assistant — Databricks App backend.

FastAPI app that:
  - Streams the Agent Bricks Multi-Agent Supervisor response token-by-token
    (Responses API, Server-Sent Events) so the UI shows the agent's thinking live.
  - Stores conversations in a Lakebase (Postgres) instance for persistence
    across sessions (Lab 4+).
  - Exposes a simple REST interface (no approval prompts — all MCP tool calls
    happen server-side inside the Supervisor, covered by the app.yaml resource
    binding which grants CAN_QUERY to the service principal at deploy time).
  - Serves a self-contained static HTML/JS frontend.

Auth: the app runs AS ITS SERVICE PRINCIPAL. databricks.sdk Config() resolves
the SP credentials the Apps runtime injects — never a hardcoded token.

Architecture mirrors the Vaillant Field Service Assistant and SEFE Trading
Assistant (Shreya's existing FEVM apps) — same FastAPI + Responses API +
Lakebase + static frontend pattern.
"""
import json
import logging
import os
import threading
import time
import uuid

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from databricks.sdk import WorkspaceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("marc-maintenance-app")

# ── Configuration ────────────────────────────────────────────────────────────
SUPERVISOR_ENDPOINT = os.environ.get("SUPERVISOR_ENDPOINT", "marc-maintenance-supervisor-endpoint")
WAREHOUSE_ID        = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
CATALOG             = os.environ.get("DATABRICKS_CATALOG", "sunny_bay_roastery")
SCHEMA              = os.environ.get("DATABRICKS_SCHEMA", "coffee_maintenance")

# Lakebase (Postgres) — conversation memory
PG_HOST     = os.environ.get("PGHOST", "")
PG_DATABASE = os.environ.get("PGDATABASE", "databricks_postgres")
PG_PORT     = int(os.environ.get("PGPORT", "5432"))

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

if IS_DATABRICKS_APP:
    _w = WorkspaceClient()
else:
    _w = WorkspaceClient(profile=os.environ.get("DATABRICKS_PROFILE", "fevm"))


def _resolve_pg_user() -> str:
    explicit = os.environ.get("PGUSER", os.environ.get("DATABRICKS_CLIENT_ID", ""))
    if explicit:
        return explicit
    try:
        return _w.current_user.me().user_name or ""
    except Exception:
        return ""


PG_USER = _resolve_pg_user()
PG_CONFIGURED = bool(PG_HOST and PG_USER)

logger.info("Supervisor endpoint: %s", SUPERVISOR_ENDPOINT)
logger.info("Lakebase: host=%s user=%s configured=%s", PG_HOST or "(unset)", PG_USER or "(unset)", PG_CONFIGURED)


def _workspace_host() -> str:
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        return host if host.startswith("http") else f"https://{host}"
    return _w.config.host


def _auth_headers() -> dict:
    return {**_w.config.authenticate(), "Content-Type": "application/json"}


# ── Lakebase connection pool ─────────────────────────────────────────────────
try:
    import psycopg
    from psycopg_pool import ConnectionPool
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    logger.warning("psycopg / psycopg_pool not installed — conversation memory disabled")

_pool: "ConnectionPool | None" = None
_pool_lock = threading.Lock()
_TOKEN_TTL = 3500  # refresh OAuth token every ~58 min
_pool_created_at = 0.0


def _lakebase_token() -> str:
    """Fresh OAuth token for Lakebase LAKEBASE_OAUTH_V1 auth."""
    creds = _w.config.authenticate()
    return creds.get("Authorization", "").removeprefix("Bearer ").strip()


def _make_pool() -> "ConnectionPool | None":
    if not PSYCOPG_AVAILABLE or not PG_CONFIGURED:
        return None
    token = _lakebase_token()
    connstr = (
        f"host={PG_HOST} port={PG_PORT} dbname={PG_DATABASE} "
        f"user={PG_USER} password={token} sslmode=require "
        "options='-c statement_timeout=30000'"
    )
    try:
        pool = ConnectionPool(connstr, min_size=1, max_size=5, open=True)
        logger.info("Lakebase connection pool created")
        return pool
    except Exception as exc:
        logger.warning("Lakebase pool creation failed: %s", exc)
        return None


def get_pool() -> "ConnectionPool | None":
    global _pool, _pool_created_at
    with _pool_lock:
        if _pool is None or time.time() - _pool_created_at > _TOKEN_TTL:
            _pool = _make_pool()
            _pool_created_at = time.time()
    return _pool


def _db_exec(sql: str, params=None):
    """Execute a SQL statement against Lakebase; silently skip if not configured."""
    pool = get_pool()
    if pool is None:
        return
    try:
        with pool.connection() as conn:
            conn.execute(sql, params or ())
            conn.commit()
    except Exception as exc:
        logger.warning("Lakebase exec failed: %s", exc)


def _db_fetch(sql: str, params=None) -> list:
    """Fetch rows from Lakebase; return [] if not configured."""
    pool = get_pool()
    if pool is None:
        return []
    try:
        with pool.connection() as conn:
            cur = conn.execute(sql, params or ())
            return cur.fetchall()
    except Exception as exc:
        logger.warning("Lakebase fetch failed: %s", exc)
        return []


def ensure_schema():
    """Create conversations + messages tables if they don't exist."""
    _db_exec("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id  TEXT PRIMARY KEY,
            title            TEXT,
            created_at       TIMESTAMPTZ DEFAULT now(),
            updated_at       TIMESTAMPTZ DEFAULT now()
        )
    """)
    _db_exec("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id       TEXT PRIMARY KEY,
            conversation_id  TEXT REFERENCES conversations(conversation_id),
            role             TEXT NOT NULL,
            content          TEXT NOT NULL,
            created_at       TIMESTAMPTZ DEFAULT now()
        )
    """)
    _db_exec("CREATE INDEX IF NOT EXISTS idx_msgs_convo ON messages(conversation_id)")


# ── Supervisor streaming ─────────────────────────────────────────────────────
def _stream_supervisor(conversation_id: str, messages: list[dict]):
    """
    Call the Agent Bricks Supervisor via the Responses API and yield SSE chunks.

    Uses the same streaming pattern as the Vaillant and SEFE apps:
    POST /serving-endpoints/{name}/invocations with stream=true,
    then forward each output item chunk as an SSE 'data:' line.

    All MCP tool calls (you.com, Genie Agent, Delta table lookups) happen
    INSIDE the Supervisor on the serving endpoint — the App never sees them
    and never prompts for approval. The app.yaml resource binding handles auth.
    """
    base = f"{_workspace_host()}/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations"
    payload = {
        "messages": messages,
        "stream": True,
        "max_tokens": 2048,
    }

    try:
        resp = requests.post(
            base,
            headers=_auth_headers(),
            data=json.dumps(payload),
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
    except requests.HTTPError as exc:
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        return

    full_response = []
    for line in resp.iter_lines():
        if not line:
            continue
        raw = line.decode("utf-8") if isinstance(line, bytes) else line
        if raw.startswith("data:"):
            raw = raw[5:].strip()
        if raw in ("[DONE]", ""):
            break
        try:
            chunk = json.loads(raw)
            # Extract text delta — handle both chat-completions and Responses API shape
            delta = (
                chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                or chunk.get("delta", {}).get("text")
                or ""
            )
            if delta:
                full_response.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
        except json.JSONDecodeError:
            pass

    # Persist to Lakebase
    assistant_text = "".join(full_response)
    if assistant_text:
        _db_exec(
            "INSERT INTO messages (message_id, conversation_id, role, content) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), conversation_id, "assistant", assistant_text),
        )
        # Update conversation timestamp
        _db_exec(
            "UPDATE conversations SET updated_at = now() WHERE conversation_id = %s",
            (conversation_id,),
        )

    yield "data: [DONE]\n\n"


# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(title="Marc's Maintenance Assistant")


@app.on_event("startup")
async def startup():
    ensure_schema()
    logger.info("App ready — supervisor: %s | lakebase: %s",
                SUPERVISOR_ENDPOINT, "configured" if PG_CONFIGURED else "NOT configured (no memory)")


# ── REST endpoints ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Send a message and stream the Supervisor response as SSE.

    If conversation_id is None, a new conversation is created.
    All prior messages for the conversation are sent as context.
    """
    if not req.message.strip():
        raise HTTPException(400, "message cannot be empty")

    convo_id = req.conversation_id or str(uuid.uuid4())

    # Create conversation record if new
    if not req.conversation_id:
        title = req.message[:60] + ("…" if len(req.message) > 60 else "")
        _db_exec(
            "INSERT INTO conversations (conversation_id, title) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (convo_id, title),
        )

    # Persist the user message
    _db_exec(
        "INSERT INTO messages (message_id, conversation_id, role, content) VALUES (%s, %s, %s, %s)",
        (str(uuid.uuid4()), convo_id, "user", req.message),
    )

    # Build message history for the Supervisor
    rows = _db_fetch(
        "SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY created_at",
        (convo_id,),
    )
    messages = [{"role": r[0], "content": r[1]} for r in rows] if rows else [
        {"role": "user", "content": req.message}
    ]

    return StreamingResponse(
        _stream_supervisor(convo_id, messages),
        media_type="text/event-stream",
        headers={
            "X-Conversation-Id": convo_id,
            "Cache-Control": "no-cache",
        },
    )


@app.get("/api/conversations")
async def list_conversations():
    """Return all conversations ordered by most recent."""
    rows = _db_fetch(
        "SELECT conversation_id, title, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 50"
    )
    return {"conversations": [
        {"id": r[0], "title": r[1], "updated_at": str(r[2])} for r in rows
    ]}


@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """Return all messages for a conversation."""
    rows = _db_fetch(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = %s ORDER BY created_at",
        (conversation_id,),
    )
    return {"messages": [
        {"role": r[0], "content": r[1], "created_at": str(r[2])} for r in rows
    ]}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "supervisor": SUPERVISOR_ENDPOINT,
        "lakebase": PG_CONFIGURED,
    }


# ── Static frontend ──────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")
