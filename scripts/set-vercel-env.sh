#!/usr/bin/env bash

ENVIRONMENT="${1:-development}"

vercel env add CRON_SECRET "$ENVIRONMENT" <<< "$CRON_SECRET"
vercel env add DEBUG "$ENVIRONMENT" <<< "$DEBUG"
vercel env add DATABASE_URL "$ENVIRONMENT" <<< "$DATABASE_URL"