@echo off

set "ENVIRONMENT=%~1"
if "%ENVIRONMENT%"=="" set "ENVIRONMENT=development"

echo %CRON_SECRET% | vercel env add CRON_SECRET %ENVIRONMENT%
echo %DEBUG% | vercel env add DEBUG %ENVIRONMENT%
echo %DATABASE_URL% | vercel env add DATABASE_URL %ENVIRONMENT%