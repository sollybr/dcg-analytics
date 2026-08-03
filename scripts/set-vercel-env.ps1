param(
    [ValidateSet("development", "production")]
    [string]$Environment = "development"
)

$CRON_SECRET | vercel env add CRON_SECRET $Environment
$DEBUG | vercel env add DEBUG $Environment
$DATABASE_URL | vercel env add DATABASE_URL $Environment