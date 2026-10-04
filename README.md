# DCG Analytics

A hybrid full-stack application for analyzing Digimon Card Game (DCG) data, built with a Django backend, Vite/React frontend, and PostgreSQL/SQLite database support.

## Architecture

DCG Analytics uses a monolithic deployment model on Vercel:

* **Backend:** Django + Django REST Framework
* **Frontend:** React + Vite
* **Database:** PostgreSQL in deployed environments, with SQLite support for local development where configured
* **Application server:** Gunicorn through Vercel's Python runtime
* **Frontend deployment:** Vite production build served through the Vercel configuration
* **Local integration:** `vercel dev` provides the same routing model used by the deployment

The frontend uses React lazy-loading for large dashboard and detail views so those modules can be emitted as separate Vite chunks instead of being included entirely in the initial bundle.

## Requirements

Install the following before setting up the project:

| Tool       | Requirement                                                            |
| ---------- | ---------------------------------------------------------------------- |
| Python     | **3.13+**                                                              |
| Node.js    | **22+**                                                                |
| pnpm       | Current supported version                                              |
| Vercel CLI | Required for local Vercel development and deployment                   |
| PostgreSQL | Required when using PostgreSQL instead of SQLite                       |
| WSL 2      | **Strongly recommended for the full `vercel dev` workflow on Windows** |

### Windows and WSL

The application can be developed with native Windows tools, but the **full monolithic `npx vercel dev` workflow is strongly recommended from WSL 2**.

Vercel's local development/build workflow can encounter platform-specific issues when run directly from Windows, particularly when the project combines the Vercel Python runtime, Django, and the frontend build.

For Windows users, use a Linux distribution through **WSL 2** and run the Vercel commands from the WSL environment:

```bash
wsl
cd /path/to/card-analyzer-dcg
npx vercel dev
```

A typical setup is:

```text
Windows
└── WSL 2
    ├── Python 3.13+
    ├── Node.js 22+
    ├── pnpm
    └── Vercel CLI
```

Keep the project inside the WSL/Linux filesystem when possible for better filesystem and tooling compatibility:

```text
~/projects/card-analyzer-dcg
```

rather than relying on a Windows-mounted path such as:

```text
/mnt/c/...
```

Native Windows remains suitable for frontend-only Vite development, editing, Git operations, and other tasks that do not require the complete Vercel local runtime.

Install the Vercel CLI globally or run it through `npx`:

```bash
npm install -g vercel
```

The Python dependency definition is maintained in `pyproject.toml`, with `uv.lock` providing the locked environment.

## Clone the Repository

```bash
git clone https://github.com/your-username/card-analyzer-dcg.git
cd card-analyzer-dcg
```

## Environment Variables

The application uses the following environment variables:

| Variable       | Purpose                                                      |
| -------------- | ------------------------------------------------------------ |
| `DATABASE_URL` | PostgreSQL connection string when running against PostgreSQL |
| `DEBUG`        | Django debug setting                                         |
| `CRON_SECRET`  | Secret used to authenticate scheduled requests               |

Environment setup scripts are provided for common shells:

```text
scripts/
├── set-vercel-env.sh
├── set-vercel-env.ps1
└── set-vercel-env.bat
```

Use the script corresponding to your environment and specify either `development` or `production`.

### PowerShell

```powershell
.\scripts\set-vercel-env.ps1 development
```

For production:

```powershell
.\scripts\set-vercel-env.ps1 production
```

The scripts expect the corresponding values to already be available as local environment variables.

To pull environment variables from the linked Vercel project instead:

```bash
npx vercel pull --environment=development
```

Do not commit `.env.local` or any other file containing database credentials, API keys, secrets, or other sensitive configuration.

## Link the Repository to Vercel

Link the local repository to the Vercel project:

```bash
npx vercel link
```

This associates the local working directory with the corresponding Vercel project.

## Backend Setup

### Using uv

`uv` is the recommended way to work with the Python environment because the project includes both `pyproject.toml` and `uv.lock`.

Create/synchronize the environment with:

```bash
uv sync
```

Activate the environment when needed.

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**WSL / macOS / Linux**

```bash
source .venv/bin/activate
```

### Using pip

A generated `requirements.txt` is also provided for environments that use pip directly.

**Windows PowerShell:**

```powershell
python -m venv myenv
myenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**WSL / macOS / Linux:**

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

The project currently requires Python **3.13 or newer**.

## Frontend Setup

Install the frontend dependencies:

```bash
cd frontend
pnpm install
```

For a production build:

```bash
pnpm run build
```

The build performs two steps:

1. Generates the Vite production output.
2. Reports generated JavaScript, MJS, and CSS chunk sizes.

Chunks larger than **500 KB** are explicitly flagged in the build output to make bundle-size regressions easier to identify.

The generated Vite output is written to:

```text
frontend/dist/
```

This directory is treated as generated build output and is excluded from Vercel uploads.

## Local Development

### Full application through Vercel

For the **full Django + Vite application**, use Vercel's local development server:

```bash
npx vercel dev
```

### Windows recommendation

On Windows, run the command from **WSL 2 rather than native PowerShell or Command Prompt**:

```bash
wsl
cd ~/projects/card-analyzer-dcg
npx vercel dev
```

This is the recommended environment when testing the complete Vercel deployment locally.

From the `frontend` directory, the project also provides a convenience script:

```bash
pnpm run vercel:dev
```

This clears the local Vercel cache before starting the root project's Vercel development server.

### Frontend-only development

For Vite development without Vercel's local routing:

```bash
cd frontend
pnpm run dev
```

This workflow can be used directly from native Windows as well as WSL/macOS/Linux.

## Database Initialization

The project provides a Django management command that performs the required database initialization and data population.

Run it from the repository root using Vercel's environment:

```bash
npx vercel env run -- python manage.py bootstrap_db
```

This allows the bootstrap process to use the configured environment variables, including `DATABASE_URL`.

When using Windows, the same command is preferably run from the WSL environment alongside `npx vercel dev`.

## Production Build

Build the frontend from the `frontend` directory:

```bash
pnpm run build
```

The production build includes chunk-size reporting. A successful build will list the generated assets and report the number of chunks exceeding the 500 KB threshold.

## Vercel Configuration

The repository contains a `vercel.json` configuration for the monolithic deployment.

The configuration:

* Builds `api/index.py` with the Vercel Python runtime.
* Builds the frontend using its `package.json`.
* Excludes local Python environments, Vercel's local directory, and generated frontend assets from the Python build context.
* Configures the application routes and scheduled functionality used by the deployment.

Local/generated directories are also excluded through `.vercelignore`, including:

```text
.venv*
.vercel
myenv*
myenv-wsl
__pycache__
node_modules
frontend/dist
```

## Project Structure

```text
.
├── api/
│   └── index.py
├── frontend/
│   ├── src/
│   ├── scripts/
│   │   └── report-chunks.mjs
│   ├── package.json
│   └── dist/
├── scripts/
│   ├── set-vercel-env.sh
│   ├── set-vercel-env.ps1
│   └── set-vercel-env.bat
├── manage.py
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── vercel.json
```

`frontend/dist/`, Python virtual environments, `.vercel/`, and other generated files are local build artifacts and should not be committed to the repository.
