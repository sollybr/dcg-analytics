# DCG Analytics: Frontend

Web app for exploring the Digimon Card Game (DCG) card database: card search, analytics charts, and statistical distributions and associations between card fields.

Built with React 19, TypeScript, Vite and pnpm. UI primitives (comboboxes, listboxes) come from React Aria Components.

## Requirements

- Node.js 22
- pnpm (enabled through Corepack: `corepack enable`)
- The Django backend running locally, for anything that loads live data

## Quick start

```bash
corepack enable
pnpm install
pnpm dev
```

The dev server prints its URL, normally `http://localhost:5173`. It must proxy `/api` to the backend (`http://localhost:8000` by default); see `server.proxy` in `vite.config.ts`.

## Scripts

| Command | What it does |
| --- | --- |
| `pnpm dev` | Start the Vite dev server with hot reload. |
| `pnpm build` | Produce the production bundle in `dist/`. |
| `pnpm preview` | Serve the production bundle locally. |
| `pnpm typecheck` | Run `tsc --noEmit`. Vite does not type-check, so run this before committing. |

## API

All requests use relative URLs, so whatever serves the frontend must route `/api/*` to the backend. In development that is the Vite proxy; in production it is whatever serves the built files (see Deployment).

| Endpoint | Used for |
| --- | --- |
| `GET /api/analytics/` | Aggregated analytics for the chart view. Accepts the filters defined in `filters.js`. |
| `GET /api/cards/?name=` | Card lookup by name. |
| `GET /api/cards-by-type/?type=&page=` | Paginated cards of one type. |
| `GET /api/field-options/?field=&q=&limit=` | Distinct values and card counts for one field, powering autocomplete. `field` is one of `name`, `color`, `rarity`, `expansion`, `subtype`, `card_type`. Default limit 20, maximum 100. |
| `GET /api/statistics/schema/` | Fields available to the statistics view. |
| `GET /api/statistics/distribution/?given=&value=&target=` | Distribution of `target` among cards where `given` equals `value`. |
| `GET /api/statistics/association/?first=&second=` | Association between two fields. |

All fetchers live in `src/api.ts`. Components should call those instead of using `fetch()` directly.

## Project structure

```text
frontend/
├── index.html
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── api.ts              # Typed API client
    ├── fieldOptions.ts     # Field names shared with the backend whitelist
    ├── cardUtils.ts        # Card types and helpers
    ├── chartUtils.ts       # Chart datasets, colors and options
    ├── autocomplete/       # ComboBox-based field autocomplete (+ CSS)
    └── components/         # Views, including AdvancedStatisticsView
```

## Conventions

- **Types:** new modules are TypeScript. Existing `.jsx` files are migrated gradually, and `allowJs` is on so both coexist.
- **Backend whitelist:** `src/fieldOptions.ts` and `FIELD_OPTION_FIELDS` in `analytics/views.py` must list the same fields. Change both together.
- **Data fetching:** keep it in `api.ts`. Pass an `AbortSignal` for requests that can be superseded, like typeahead.
- **Accessibility:** use React Aria components for interactive controls so keyboard navigation and ARIA roles work by default.

## Deployment

This folder is deployment-agnostic. `pnpm build` produces a static bundle in `dist/`, and any host can serve it if it meets these requirements:

- `dist/` is served as the site root.
- Unknown paths fall back to `index.html`, because routing happens in the browser.
- `/api/*` is forwarded to the Django backend on the same origin. The app uses relative URLs and has no configurable API base URL.

How `dist/` is built, hosted and wired to the backend is set up outside this folder. For platform-specific configuration (hosting, environment variables, scheduled jobs), see the root README.