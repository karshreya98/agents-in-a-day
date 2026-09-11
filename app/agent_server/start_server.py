import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from mlflow.genai.agent_server import AgentServer, setup_mlflow_git_based_version_tracking

# Load env vars from .env before importing the agent for proper auth
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

# Need to import the agent to register the functions with the server
import agent_server.agent  # noqa: E402

agent_server = AgentServer("ResponsesAgent", enable_chat_proxy=True)

# Define the app as a module level variable to enable multiple workers
app = agent_server.app  # noqa: F841
setup_mlflow_git_based_version_tracking()

# ── Lakebase-backed short-term memory ─────────────────────────────
from databricks_langchain import AsyncCheckpointSaver

from agent_server import dispatch

_original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def _lifespan(app):
    # Local/dev or sample-data mode (AGENT_DRY_RUN): keep the in-memory MemorySaver.
    if not os.getenv("DATABRICKS_APP_NAME") or os.getenv("AGENT_DRY_RUN"):
        async with _original_lifespan(app):
            yield
        return
    # Deployed (not dry-run): durable short-term memory on autoscaling Lakebase.
    async with AsyncCheckpointSaver(
        project=os.environ["LAKEBASE_AUTOSCALING_PROJECT"],
        branch=os.getenv("LAKEBASE_AUTOSCALING_BRANCH", "production"),
        schema="agent_memory",   # REQUIRED — the app SP can't write to `public`
    ) as checkpointer:
        await checkpointer.setup()                           # REQUIRED — creates the tables
        dispatch.GRAPH = dispatch.build_graph(checkpointer)  # rebind graph to Lakebase memory
        async with _original_lifespan(app):
            yield


app.router.lifespan_context = _lifespan


def main():
    agent_server.run(app_import_string="agent_server.start_server:app")

