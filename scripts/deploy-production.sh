#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

load_env() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  set -a
  # shellcheck disable=SC1090
  source "$file"
  set +a
}

load_env "$ROOT/.env"
load_env "$ROOT/backend/.env"

echo "==> Verifying Supabase connection"
python3 "$ROOT/scripts/verify-supabase.py"

BACKEND_URL="${NEXT_PUBLIC_API_URL:-https://xeno-crm-backend.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://xeno-fde-ten.vercel.app}"

echo "==> Syncing Vercel production env vars"
cd "$ROOT/frontend"

upsert_env() {
  local name="$1"
  local value="$2"
  vercel env rm "$name" production --yes 2>/dev/null || true
  printf '%s' "$value" | vercel env add "$name" production
}

upsert_env "NEXT_PUBLIC_API_URL" "$BACKEND_URL"
upsert_env "NEXT_PUBLIC_SUPABASE_URL" "${NEXT_PUBLIC_SUPABASE_URL:-$SUPABASE_PROJECT_URL}"
upsert_env "NEXT_PUBLIC_SUPABASE_ANON_KEY" "${NEXT_PUBLIC_SUPABASE_ANON_KEY:-$SUPABASE_PUBLISHABLE_KEY}"

echo "==> Deploying frontend to Vercel (production)"
vercel --prod --yes

echo
echo "Production URLs:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo
echo "Next steps:"
echo "  1. Deploy backend + channel service on Render using render.yaml"
echo "  2. Set Render DATABASE_URL to your Supabase transaction pooler URI (port 6543)"
echo "  3. Seed production data once: curl -X POST $BACKEND_URL/seed"
