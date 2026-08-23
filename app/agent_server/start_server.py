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

# --- Lab 3 · Task 3: durable short-term memory on Lakebase (rebinds dispatch.GRAPH) ---
import logging  # noqa: E402
import os  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from databricks_langchain import AsyncCheckpointSaver  # noqa: E402

from agent_server import dispatch  # noqa: E402

_original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def _lifespan(app):
    # Local/dev (not deployed as a Databricks App): keep the in-memory MemorySaver.
    if not os.getenv("DATABRICKS_APP_NAME"):
        async with _original_lifespan(app):
            yield
        return
    # Deployed: durable short-term memory on the pre-created Lakebase instance.
    # Fail soft: if Lakebase can't be reached, stay up on in-memory memory instead of crashing.
    try:
        async with AsyncCheckpointSaver(instance_name="sunny-bay-lakebase") as checkpointer:
            await checkpointer.setup()                           # REQUIRED - creates the tables
            dispatch.GRAPH = dispatch.build_graph(checkpointer)  # rebind graph to Lakebase memory
            async with _original_lifespan(app):
                yield
    except Exception as e:
        logging.getLogger(__name__).warning(
            "Lakebase unavailable, falling back to in-memory memory: %s", e)
        async with _original_lifespan(app):
            yield


app.router.lifespan_context = _lifespan


def main():
    agent_server.run(app_import_string="agent_server.start_server:app")
