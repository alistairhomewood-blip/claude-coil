# Deploy Checklist — Vercel (frontend) + Render (backend)

> Scope: going from localhost dev to public production URLs.
> Do **not** use this checklist for merging unreviewed feature branches.

---

## 0. Pre-flight: update placeholder URLs in tracked files

Two values in the repo are placeholders and **must** be replaced before the first live deploy.

| File | Key / location | Placeholder | Replace with |
|------|---------------|-------------|--------------|
| `render.yaml` | `envVars[ALLOWED_ORIGINS].value` | `https://your-frontend.vercel.app` | your Vercel production URL |
| `vercel.json` | `rewrites[0].destination` | `https://coil-geometry-api.onrender.com/api/:path*` | `https://<your-render-service>.onrender.com/api/:path*` |
| `vercel.json` | `env.VITE_API_BASE_URL` | `https://coil-geometry-api.onrender.com` | `https://<your-render-service>.onrender.com` |

**Circular dependency:** you need the Render URL to fill in `vercel.json`, and the Vercel URL to fill in `render.yaml`.
Resolution: deploy Render first (step 1), copy the `.onrender.com` URL, then set it in `vercel.json` before the Vercel deploy (step 2), then go back and update `ALLOWED_ORIGINS` in Render env vars (step 3).

---

## 1. Branch merge order

Merge in this order to avoid broken builds on `main`:

```
feat-validation   →  main    # schema/contract validation; API depends on it
feat-deploy       →  main    # this branch; render.yaml + vercel.json + api/main.py
feat-frontend     →  main    # UI code (merge only when frontend is ready to ship)
```

**Hold** these branches until separately reviewed — do not merge for the initial public launch:
- `feat-elongated-toroid`
- `feat-project-io`
- `feat-frontend-ui`

---

## 2. Render dashboard steps (backend)

1. Go to **render.com > New > Web Service**.
2. Connect your GitHub repo and select the `main` branch.
3. Set **Root Directory**: `physics`
4. Set **Runtime**: Python 3
5. Set **Build command**: `pip install -e .`
6. Set **Start command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
7. Set **Health Check Path**: `/api/health`
8. Add env vars (see [section 4](#4-required-env-vars)):
   - `ALLOWED_ORIGINS` → your Vercel URL (can be set after Vercel deploy — see circular dependency note above)
   - `APP_VERSION` → `0.1.0`
   - `SCHEMA_VERSION` → `1.0.0`
9. Click **Save & Deploy**.
10. Wait for the build log to show `Application startup complete`.
11. **Copy the service URL** — looks like `https://coil-geometry-api.onrender.com`.

> Render free tier spins down after 15 min of inactivity. The first request after sleep takes ~30 s. Upgrade to a paid plan to keep the service always-on.

---

## 3. Vercel dashboard steps (frontend)

1. Go to **vercel.com > New Project**.
2. Import the GitHub repo, select the `main` branch.
3. Set **Root Directory** to wherever the frontend code lives (e.g. `apps/web`).
4. Framework preset: **Vite** (auto-detected if `vite.config.*` is present).
5. Under **Environment Variables**, add `VITE_API_BASE_URL` → `https://<your-render-service>.onrender.com` (the URL from step 2.11).
6. Click **Deploy**.
7. **Copy the production URL** — looks like `https://coil-geometry.vercel.app`.
8. Go back to Render and update `ALLOWED_ORIGINS` to this URL (closes the circular dependency).
9. Commit + push the updated `render.yaml` (ALLOWED_ORIGINS) and `vercel.json` (Render URLs) to `main`.

---

## 4. Required env vars

### Render (backend)

| Var | Production value | Dev default | Notes |
|-----|-----------------|-------------|-------|
| `ALLOWED_ORIGINS` | `https://<project>.vercel.app` | `http://localhost:5173` | Comma-separated; add preview-deploy subdomains if needed |
| `APP_VERSION` | `0.1.0` | `0.1.0-dev` | Must match `[project].version` in `physics/pyproject.toml` |
| `SCHEMA_VERSION` | `1.0.0` | `1.0.0` | Bump when `project_file.schema.json` adds/removes required fields |

### Vercel (frontend)

| Var | Production value | Dev default | Notes |
|-----|-----------------|-------------|-------|
| `VITE_API_BASE_URL` | `https://<your-render-service>.onrender.com` | `http://localhost:8000` | Also used as the rewrite destination in `vercel.json` |

---

## 5. Switch from localhost to public URLs

Every value that changes when going from local dev to production:

| Location | Localhost value | Production value |
|----------|----------------|-----------------|
| `ALLOWED_ORIGINS` (Render env) | `http://localhost:5173` | `https://<project>.vercel.app` |
| `VITE_API_BASE_URL` (Vercel env) | `http://localhost:8000` | `https://<your-render-service>.onrender.com` |
| `vercel.json` rewrite destination | *(not used locally)* | `https://<your-render-service>.onrender.com/api/:path*` |
| `physics/.env` `ALLOWED_ORIGINS` | `http://localhost:5173` | *(not committed; keep localhost in local .env)* |

**Local dev** uses `scripts/dev_start.sh` which sets `ALLOWED_ORIGINS=http://localhost:5173` and starts uvicorn on port 8000. No changes to that script are needed for production.

---

## 6. Smoke-test commands

The script exits 0 if all checks pass, non-zero if any fail. It tests: HTTP 200 on `/api/health`, version fields present, CORS preflight headers, and 405 on disallowed methods.

```bash
# 1. Test production backend directly (bypasses Vercel proxy)
API_BASE=https://<your-render-service>.onrender.com \
CORS_ORIGIN=https://<project>.vercel.app \
bash scripts/smoke_test.sh

# 2. Test via Vercel proxy (end-to-end path)
API_BASE=https://<project>.vercel.app \
CORS_ORIGIN=https://<project>.vercel.app \
bash scripts/smoke_test.sh

# 3. Test local backend (development)
API_BASE=http://localhost:8000 bash scripts/smoke_test.sh
```

Run test 1 immediately after Render deploys, then test 2 after Vercel deploys. Both must exit 0 before considering the deployment done.

---

## 7. Rollback

### Backend (Render)
- Dashboard > your service > **Deploys** tab.
- Click any previous successful deploy > **Rollback to this deploy**.
- Takes ~1 minute. Health check at `/api/health` confirms recovery.

### Frontend (Vercel)
- Dashboard > your project > **Deployments** tab.
- Find the last good deployment > three-dot menu > **Promote to Production**.
- Takes effect instantly (CDN re-points).

### Config-only rollback (env var mistake)
- Edit the env var directly in the Render or Vercel dashboard — no redeploy needed for env var changes on Render; Vercel requires a redeploy.
- Or: `git revert <commit-sha>` on the commit that changed `ALLOWED_ORIGINS` / `VITE_API_BASE_URL`, push to trigger auto-redeploy.

### Do NOT revert
The `render.yaml` start command was changed from `uvicorn physics.api.main:app` to `uvicorn api.main:app` (the old path was wrong given `rootDir: physics`). Reverting this will break the backend startup.

---

## 8. Post-deploy verification checklist

- [ ] `GET https://<render-url>/api/health` returns `{"status":"ok", "physics":"ok", ...}`
- [ ] `GET https://<render-url>/api/version` returns correct `appVersion` and `schemaVersion`
- [ ] Smoke test 1 exits 0 (direct backend)
- [ ] Smoke test 2 exits 0 (via Vercel proxy)
- [ ] Frontend loads and makes a successful API call (check browser DevTools Network tab)
- [ ] No CORS errors in browser console
- [ ] `render.yaml` and `vercel.json` committed with real URLs (no more placeholders)
