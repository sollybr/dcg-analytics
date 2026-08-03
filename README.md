# DCG Analytics

A hybrid approach, full-stack application for analyzing Digimon Card Game (DCG) data, built with a Django backend, Vite frontend, and PostgreSQL/SQLite database.

## Architecture

This application is configured for a monolithic server deployment on Vercel, hosting both the Django backend API and the Vite frontend within a single deployment target.

## Prerequisites

Ensure you have the following installed on your system:

- [Python 3.12 or higher](https://www.python.org/downloads/)

- [Node.js (v22+ required — older versions will cause dependency failures)](https://nodejs.org/)

- [pnpm package manager](https://pnpm.io/installation)

- [Vercel CLI](https://vercel.com/docs/cli) (global installation: `npm i -g vercel`)

## Installation and Setup Instructions

### 1. Clone the Repository

Bash

```
git clone https://github.com/your-username/card-analyzer-dcg.git
cd card-analyzer-dcg
```

### 2. Set Up Environment Variables

Link your local repository to your Vercel project to pull the necessary environment variables (including your database connection string and cron secret):

Bash

```
npx vercel link
npx vercel env pull .env.local
```

### 3. Backend Setup (Django)

Create and activate a Python virtual environment, then install the required dependencies:

- **Windows (PowerShell):**
  
  PowerShell
  
  ```
  python -m venv myenv
  myenv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- **macOS / Linux:**
  
  Bash
  
  ```
  python3 -m venv myenv
  source myenv/bin/activate
  pip install -r requirements.txt
  ```

### 4. Frontend Setup

Install the required frontend dependencies using `pnpm`:

Bash

```
pnpm install
```

### 5. Database Initialization and Data Synchronization

To streamline setup, the application includes a custom management command that automatically runs database migrations and populates the database with card records.

Run the bootstrap command using the Vercel execution context to ensure it reads your environment variables:

PowerShell

```
npx vercel env run -- python manage.py bootstrap_db
```

## Running the Application Locally

To run the monolithic development server locally (which simultaneously serves both the Django backend and the Vite frontend using Vercel's local routing):

Bash

```
npx vercel dev
```
