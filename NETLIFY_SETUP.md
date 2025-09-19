# Netlify Deployment Guide for Skreenit Subdomains

This guide shows how to deploy your reorganized frontend to Netlify with dedicated sites per subdomain, plus shared assets hosted under the `auth` subdomain.

## Subdomains and Publish Directories

Create the following Netlify sites from this repository. For each site, set the Publish directory as shown, and map the custom domain accordingly.

- www.skreenit.com
  - Publish directory: `www/`
  - Custom domain: `www.skreenit.com`

- login.skreenit.com
  - Publish directory: `login/`
  - Custom domain: `login.skreenit.com`

- applicants.skreenit.com
  - Publish directory: `applicants/`
  - Custom domain: `applicants.skreenit.com`

- recruiter.skreenit.com
  - Publish directory: `recruiter/`
  - Custom domain: `recruiter.skreenit.com`

- dashboards.skreenit.com
  - Publish directory: `dashboards/`
  - Custom domain: `dashboards.skreenit.com`

- auth.skreenit.com
  - Publish directory: `auth/`
  - Custom domain: `auth.skreenit.com`

Shared assets are hosted under `auth.skreenit.com` at `/assets/`.
All subdomains reference assets using absolute URLs like `https://auth.skreenit.com/assets/css/dashboard-styles.css` and images under `https://auth.skreenit.com/assets/images/`.

No build command is needed for these static sites.

## DNS Configuration

Point the following DNS records (in your DNS provider) to Netlify:

- Create CNAME records for each subdomain:
  - `www` → `your-netlify-site-subdomain.netlify.app`
  - `login` → `...netlify.app`
  - `applicants` → `...netlify.app`
  - `recruiter` → `...netlify.app`
  - `dashboards` → `...netlify.app`
  - `auth` → `...netlify.app`
  - (No separate static site is needed, assets are served from `auth`)

Netlify UI will guide you to the exact `netlify.app` target for each site under Domain settings.

Enable HTTPS for each site after DNS is verified (Netlify → Domain management → HTTPS → Enable automatic). 

## Environment Variables (Frontend)

Frontend pages do not require Netlify environment variables because Supabase credentials are imported in-browser via `auth/assets/js/supabase-config.js`. Ensure the values there match your Supabase project (or replace with environment-driven injection in future).

## Backend (Render) Configuration

The backend is already updated to be compatible with all subdomains:

- `backend/main.py`: default `FRONTEND_BASE_URL=https://login.skreenit.com` and email template uses that base URL.
- `backend/render.yaml` (and `.env.example`) include all subdomains in `ALLOWED_ORIGINS`, including `https://auth.skreenit.com`.

On Render:
- Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- Set `RESEND_API_KEY`, `EMAIL_FROM`
- Set `FRONTEND_BASE_URL=https://login.skreenit.com`
- Set `ALLOWED_ORIGINS` to the list shown in repo config

## Supabase Auth Redirects

In Supabase Dashboard → Authentication → URL Configuration:
- Site URL: `https://login.skreenit.com`
- Additional Redirect URLs (one per line):
  - `https://login.skreenit.com/*`
  - `https://applicants.skreenit.com/*`
  - `https://recruiter.skreenit.com/*`
  - `https://dashboards.skreenit.com/*`
  - `https://auth.skreenit.com/*`
  - For local dev: `http://localhost:8000/*` (optional)

## Local Development

Serve from repository root to preview structure quickly:

```bash
python -m http.server 8000
```

Then visit:
- `http://localhost:8000/www/`
- `http://localhost:8000/login/`
- `http://localhost:8000/applicants/`
- etc.

Note: In local testing, the HTML pages point to `https://auth.skreenit.com/...` for assets. If you haven't deployed the `auth` site yet, change those links temporarily to relative paths (`../assets/...`) for local development or serve `auth/assets/` with a local static server.

## Optional: Netlify Redirects

Current pages are pure static and rely on hash-based routing or direct links. If you later add client-side routers that need clean URLs, add a `_redirects` file per site with:

```
/* /index.html 200
```

## Verification Checklist

- Each subdomain loads and uses SSL (HTTPS)
- Shared assets load from `https://auth.skreenit.com`

## Step-by-step (recommended order)

1. Create and deploy `auth` site first.
   - Publish directory: `auth/`
   - Ensure these exist and are reachable after deploy:
     - `https://auth.skreenit.com/assets/css/dashboard-styles.css`
     - `https://auth.skreenit.com/assets/css/application-form-styles.css`
     - `https://auth.skreenit.com/assets/js/auth-pages.js`
     - `https://auth.skreenit.com/assets/js/application-form.js`
     - `https://auth.skreenit.com/assets/images/logo.png`
     - `https://auth.skreenit.com/assets/images/logobrand.png`

2. Deploy remaining subdomains with the listed Publish directories.

3. In Supabase → Authentication → URL Configuration, set Site URL to `https://login.skreenit.com` and add additional redirect URLs for all listed subdomains.

4. Verify via the checklist below.

## Link Validation Checklist

- Top-left logo appears at 48px on:
  - `www/index.html`
  - `auth/login.html`, `auth/registration.html`, `auth/update-password.html`
  - `applicants/detailed-application-form.html`
  - `dashboards/index.html`, `dashboards/candidate-dashboard.html`, `dashboards/recruiter-dashboard.html`
  - `recruiter/index.html`
- Banners appear on `auth/login.html` (logobrand.png)
- CSS loads from `https://auth.skreenit.com/assets/css/*`
- JS loads from `https://auth.skreenit.com/assets/js/*` where intended (auth-pages, application-form)
- Role redirects work:
  - Login → first-time → update password → redirect to `https://login.skreenit.com/`
  - Candidate login → applicants form → success → `https://dashboards.skreenit.com/candidate-dashboard.html`
  - Recruiter login → `https://recruiter.skreenit.com/` and dashboards as needed
- Login → redirects users based on role to applicants/recruiter
- `dashboards.skreenit.com` → redirects to the right dashboard based on session
- Emails from backend link to `https://login.skreenit.com`
- Supabase auth flows return to one of the allowed subdomains

If you want, I can also prepare minimal `_redirects` files and Netlify configuration files per folder.
