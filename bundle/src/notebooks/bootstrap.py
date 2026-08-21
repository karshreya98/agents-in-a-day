# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 Agents in a Day — one-click bootstrap
# MAGIC
# MAGIC Run this **once** to stand up the whole workshop. It:
# MAGIC 1. **Creates the catalog** (default `sunny_bay_roastery`) — or reuses it if it
# MAGIC    already exists / an admin pre-created it.
# MAGIC 2. **Deploys the bundle** (the setup job + both Lakeflow pipelines).
# MAGIC 3. **Runs the setup job** end-to-end (maintenance tables, sales star schema +
# MAGIC    metric view, pre-built Sales Genie, dashboard, and the fault-report PDFs +
# MAGIC    `fault_reports_structured`).
# MAGIC 4. **Pre-creates the Lakebase instance** (`sunny-bay-lakebase`) that Lab 3's agent
# MAGIC    uses for durable short-term memory.
# MAGIC
# MAGIC **Why a bootstrap notebook and not just "Deploy"?** A Lakeflow pipeline's target
# MAGIC `catalog` is validated by Unity Catalog **at bundle-deploy time** — which is
# MAGIC *earlier* than any job task can run. So the catalog has to exist before deploy.
# MAGIC On Default-Storage / Free-Edition workspaces the catalog can only be made with
# MAGIC SQL `CREATE CATALOG` (the catalog REST API needs a storage root that isn't
# MAGIC there), so a DABs `catalogs:` resource can't do it either. This notebook creates
# MAGIC the catalog with SQL first, then deploys — one ordered, Free-Edition-safe path.
# MAGIC
# MAGIC > **Just want the maintenance tables?** You don't need this notebook — open
# MAGIC > `Lab 0 - Setup` and Run All. This bootstrap is for the *full* workshop.

# COMMAND ----------

# The catalog to create/use. On a shared workshop, give each person their own name
# so their tables don't collide. Must match what you'd otherwise set in databricks.yml.
dbutils.widgets.text("catalog", "sunny_bay_roastery")
catalog = dbutils.widgets.get("catalog").strip()

# Which bundle target to deploy. `dev` is the only target and the default.
dbutils.widgets.text("target", "dev")
target = dbutils.widgets.get("target").strip() or "dev"

if not catalog:
    raise ValueError("Set the 'catalog' widget to a catalog name (default sunny_bay_roastery).")

# COMMAND ----------

# MAGIC %md ## 1. Create the catalog (or reuse an existing one)

# COMMAND ----------

# Same create-or-use logic the old `init` job task used, but run here — before deploy.
# CREATE CATALOG works on Free Edition (SQL path); if creation is restricted (locked-down
# workspace where an admin pre-provisions catalogs), fall back to USE. Only fail if the
# catalog can neither be created nor accessed.
try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
    print(f"✅ Catalog ready (created or already existed): {catalog}")
except Exception as create_err:
    try:
        spark.sql(f"USE CATALOG `{catalog}`")
        print(f"✅ Catalog `{catalog}` already exists and is usable "
              f"(creation was restricted, using the existing one).")
    except Exception as use_err:
        raise RuntimeError(
            f"Cannot create or access catalog `{catalog}`.\n"
            f"  - creation failed: {create_err}\n"
            f"  - access failed:   {use_err}\n"
            "Ask an admin to create it (or grant you CREATE CATALOG), or set the "
            "'catalog' widget to a catalog you can write to."
        ) from use_err

# COMMAND ----------

# MAGIC %md ## 2. Locate the bundle and install the Databricks CLI

# COMMAND ----------

import os
import re
import subprocess
import tempfile

# This notebook lives at <repo>/bundle/src/notebooks/bootstrap.py inside the Git Folder,
# so the bundle root (where databricks.yml lives) is two directories up.
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
notebook_path = "/Workspace" + ctx.notebookPath().get()
bundle_root = os.path.abspath(os.path.join(os.path.dirname(notebook_path), "..", ".."))

if not os.path.exists(os.path.join(bundle_root, "databricks.yml")):
    raise RuntimeError(
        f"databricks.yml not found at {bundle_root}. This notebook must run from inside "
        "the cloned Git Folder (bundle/src/notebooks/bootstrap). If you copied it "
        "elsewhere, move it back next to the bundle/ tree."
    )
print(f"Bundle root: {bundle_root}")

# Install the CLI. The setup script chooses its own bin dir and prints
# "Installed Databricks CLI vX.Y.Z at <path>." — parse that path.
_install_dir = tempfile.mkdtemp(prefix="dbcli_")
_p = subprocess.run(
    ["bash", "-c",
     f"curl -fsSL -m 90 https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh "
     f"| sh -s -- {_install_dir}"],
    capture_output=True, text=True,
)
_m = re.search(r"Installed Databricks CLI \S+ at (\S+?)\.?$", _p.stdout.strip(), re.M)
if _m and os.path.exists(_m.group(1)):
    CLI = _m.group(1)
elif os.path.exists(os.path.join(_install_dir, "databricks")):
    CLI = os.path.join(_install_dir, "databricks")
else:
    _which = subprocess.run(["bash", "-c", "command -v databricks || true"],
                            capture_output=True, text=True).stdout.strip()
    CLI = _which if _which and os.path.exists(_which) else None

if not CLI:
    raise RuntimeError(f"Could not install the Databricks CLI.\nstdout={_p.stdout}\nstderr={_p.stderr}")

_ver = subprocess.run([CLI, "--version"], capture_output=True, text=True).stdout.strip()
print(f"✅ {_ver} at {CLI}")

# COMMAND ----------

# MAGIC %md ## 3. Authenticate with the notebook's own token

# COMMAND ----------

# The CLI picks up DATABRICKS_HOST / DATABRICKS_TOKEN from the environment — the running
# user's own workspace credentials, so deploy/run act as them (exactly what we want).
cli_env = dict(
    os.environ,
    DATABRICKS_HOST=ctx.apiUrl().get(),
    DATABRICKS_TOKEN=ctx.apiToken().get(),
    # Deploying from a Git Folder: skip the "you have uncommitted changes" guard.
    DATABRICKS_BUNDLE_ROOT=bundle_root,
)


def run_cli(args, **kw):
    """Run the CLI streaming combined output into the notebook, raise on failure."""
    print(f"$ databricks {' '.join(args)}")
    proc = subprocess.Popen(
        [CLI, *args], cwd=bundle_root, env=cli_env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"`databricks {' '.join(args)}` failed (exit {proc.returncode}).")


run_cli(["current-user", "me", "-o", "json"])

# COMMAND ----------

# MAGIC %md ## 3b. Pre-create the Lakebase instance (Lab 3 short-term memory)
# MAGIC Lab 3 gives Marc's agent durable short-term memory on **Lakebase**. Kick off the
# MAGIC instance now (non-blocking) so it's provisioned well before you reach Lab 3.

# COMMAND ----------

# Idempotent and non-fatal: only Lab 3 uses this, so a failure here (e.g. Lakebase not
# available in this region) must not break the rest of the workshop.
LAKEBASE_INSTANCE = "sunny-bay-lakebase"
_exists = subprocess.run(
    [CLI, "database", "get-database-instance", LAKEBASE_INSTANCE],
    cwd=bundle_root, env=cli_env, capture_output=True, text=True,
)
if _exists.returncode == 0:
    print(f"✅ Lakebase instance already exists: {LAKEBASE_INSTANCE}")
else:
    try:
        run_cli(["database", "create-database-instance", LAKEBASE_INSTANCE,
                 "--capacity", "CU_1", "--no-wait"])
        print(f"✅ Creating Lakebase instance '{LAKEBASE_INSTANCE}' (provisioning in the "
              "background; ready well before Lab 3).")
    except Exception as e:
        print(f"⚠️  Could not create Lakebase instance '{LAKEBASE_INSTANCE}': {e}\n"
              "    Lab 3's memory task needs it — create it manually "
              "(Compute → Database instances → Create) or skip that task.")

# COMMAND ----------

# MAGIC %md ## 3c. Install the Lab 3 memory skill for Genie Code
# MAGIC Genie Code loads skills from your **`.assistant/skills/`** folder. Copy the repo's
# MAGIC `add-lakebase-short-term-memory` skill there so Lab 3's one-line prompt just works.

# COMMAND ----------

# Non-fatal: if this can't write, Lab 3 tells you how to add the skill by hand.
import pathlib
import shutil

_user = spark.sql("SELECT current_user()").first()[0]
_skill = "add-lakebase-short-term-memory"
_src = pathlib.Path(bundle_root).parent / "app" / ".claude" / "skills" / _skill / "SKILL.md"
_dst = pathlib.Path(f"/Workspace/Users/{_user}/.assistant/skills/{_skill}")
try:
    _dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(_src, _dst / "SKILL.md")
    print(f"✅ Installed Genie Code skill '{_skill}' at {_dst}")
except Exception as e:
    print(f"⚠️  Could not install the Genie Code skill: {e}\n"
          f"    In Lab 3, open Genie Code → Settings → 'Open skills folder' and copy "
          f"app/.claude/skills/{_skill}/SKILL.md into it manually.")

# COMMAND ----------

# MAGIC %md ## 4. Deploy the bundle
# MAGIC Passes the catalog you chose above so the pipelines target the catalog we just created.

# COMMAND ----------

run_cli(["bundle", "deploy", "-t", target, "--var", f"catalog={catalog}", "--force-lock"])
print("✅ Bundle deployed.")

# COMMAND ----------

# MAGIC %md ## 5. Run the setup job end-to-end
# MAGIC This is the long one (~15–20 min): it builds every table, the metric view, the
# MAGIC Sales Genie, the dashboard, and parses the fault-report PDFs. When this cell
# MAGIC finishes green, the whole workshop is ready.

# COMMAND ----------

run_cli(["bundle", "run", "agents_in_a_day_setup", "-t", target,
         "--var", f"catalog={catalog}", "--restart"])
print(f"\n🎉 All set. Everything is in catalog `{catalog}`. Head to Lab 1.")
