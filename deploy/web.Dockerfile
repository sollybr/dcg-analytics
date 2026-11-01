FROM node:26.12.1-alpine3.24 AS build
RUN npm install -g pnpm@12.3.4
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml* frontend/.npmrc* ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL
RUN pnpm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY deploy/Caddyfile /etc/caddy/Caddyfile
