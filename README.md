# DCG Analytics

A hybrid full-stack application for analyzing Digimon Card Game (DCG) data, built with a Django backend, Vite frontend, and PostgreSQL/SQLite database.

## Architecture

This application is configured for a monolithic server deployment on Vercel, hosting both the Django backend API and the Vite frontend within a single deployment target.

## Prerequisites

Ensure you have the following installed on your system:

* [Python 3.12 or higher](https://www.python.org/downloads/)
* [Node.js (v22+ required)](https://nodejs.org/)
* [pnpm package manager](https://pnpm.io/installation)
* [Vercel CLI](https://vercel.com/docs/cli) (global installation: `npm i -g vercel`)

## Installation and Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/card-analyzer-dcg.git
cd card-analyzer-dcg
```

### 2. Link the Repository to Vercel

Link the local repository to the Vercel project:

```bash
npx vercel link
```

This associates the local project with the corresponding Vercel deployment.

### 3. Set Up Environment Variables

The application requires the following environment variables:

* `CRON_SECRET` — secret used to authenticate scheduled requests
* `DEBUG` — Django debug setting
* `DATABASE_URL` — PostgreSQL connection string

Scripts for setting these variables are provided in the `scripts/` directory:

```text
scripts/
├── set-vercel-env.sh
├── set-vercel-env.ps1
└── set-vercel-env.bat
```

Use the script corresponding to your shell and specify either `development` or `production`.

For local tests, with PowerShell, you can use:

```powershell
.\scripts\set-vercel-env.ps1 development
```

For deployment:

```powershell
.\scripts\set-vercel-env.ps1 production
```

The scripts expect the corresponding values to already be available as local environment variables.

To pull the existing environment variables from Vercel into local instead:

```bash
npx vercel pull --environment=development
```

> **Note:** Do not commit `.env.local` or any other file containing database credentials or secrets to the repository.

### 4. Backend Setup (Django)

Create and activate a Python virtual environment, then install the required dependencies.

**Windows (PowerShell):**

```powershell
python -m venv myenv
myenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 5. Frontend Setup

Install the required frontend dependencies using `pnpm`:

```bash
cd frontend
pnpm install
```

### 6. Database Initialization and Data Synchronization

To streamline setup, the application includes a custom management command that automatically runs database migrations and populates the database with card records.

Run the bootstrap command using the Vercel execution context so that it has access to the configured environment variables:

```bash
npx vercel env run -- python manage.py bootstrap_db
```

## Running the Application Locally

To run the monolithic development server locally, using Vercel's local routing to serve both the Django backend and Vite frontend:

```bash
npx vercel dev
```

This allows the local application to run using the same routing structure as the Vercel deployment.
