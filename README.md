# LinkedIn Profile API

> Reverse-engineered LinkedIn profile scraper. **No browser automation** — it
> talks directly to LinkedIn's internal *Voyager* REST API (the same endpoint
> their own web frontend calls). Given a LinkedIn profile URL or slug, it
> returns structured JSON: name, headline, location, about, experience,
> education, skills, certifications, languages, profile images, and contact info.

Built for the **Tross Software Engineer** take-home challenge.

---

## Approach (the reverse-engineering part)

LinkedIn does not expose profile data through any official API for general use.
The path used here was **discovered from live network traffic**, not docs:

1. **Capture.** Log into LinkedIn in a normal browser, open a public profile, and
   watch DevTools → Network → XHR. The frontend issues a `GET` to
   `https://www.linkedin.com/voyager/api/identity/dash/profiles` with query
   `q=memberIdentity&memberIdentity={slug}&decorationId=...`.
2. **Auth recipe** (the bit naive scrapers get wrong → `403 CSRF check failed`):
   - `li_at` — login session cookie
   - `JSESSIONID` — CSRF session cookie, **same session**
   - `csrf-token` header **must equal `JSESSIONID` with surrounding quotes stripped**
   - headers: `x-restli-protocol-version: 2.0.0`,
     `accept: application/vnd.linkedin.normalized+json+2.1`, `x-li-lang: en_US`
3. **Response shape.** A flat `included[]` array. The primary profile has an
   `entityUrn` containing `fsd_profile:` and a `firstName`. Experience / Education
   / Skills / Certifications / Languages are sibling entries keyed by their
   `$type` suffix.
4. **Two endpoints.** `dash/profiles` (primary profile + most fields) and
   `profileContactInfo` (email / websites / twitter — gated, often empty).

See [`linkedin_scraper.py`](linkedin_scraper.py) for the full commented derivation.

**Design decisions a reviewer should notice:**
- A **thin, dependency-light client** is written by hand rather than depending on
  the unmaintained `linkedin-api` PyPI package (last release 2019, logs in via
  email+password, triggers 2FA CHALLENGE, sleeps 2–5s per request). Owning the
  client demonstrates the Voyager mechanics directly.
- **Graceful failure** is bounded: 401/403 → "refresh cookies", 404 → not found,
  429 → rate limited, 5xx/timeout → upstream error. No raw tracebacks leak.
- **Resilience:** one reused `requests.Session`, a bounded TTL cache (fewer Li
  hits → lower ban risk), and a single retry on transient upstream errors.
- **HFT lens applied honestly:** this is a demo, not a trading system — the lens
  drives *discipline* (critical-path focus, bounded failure, prove-it testing),
  not microsecond latency.

---

## API

Base URL: `https://<your-host>` (see Deploy).

| Method | Path | Params | Returns |
|---|---|---|---|
| GET | `/` | — | service info |
| GET | `/health` | — | `{status, auth_configured, epoch}` |
| GET | `/profile` | `url` *or* `slug` | `ProfileResponse` |
| POST | `/profile` | JSON `{url\|slug}` | `ProfileResponse` |

### Example
```bash
curl "https://<host>/profile?slug=satyanadella"
```
```json
{
  "status": "success",
  "source": "linkedin_voyager_api",
  "fetched_at": "2026-08-30T03:10:00Z",
  "data": {
    "basic": {"first_name": "Satya", "last_name": "Nadella", "full_name": "Satya Nadella",
              "headline": "Chairman and CEO at Microsoft", "location": "Redmond, WA",
              "industry": "Technology", "public_id": "satyanadella",
              "profile_url": "https://www.linkedin.com/in/satyanadella"},
    "about": "...",
    "experience": [{"title": "Chairman and CEO", "company": "Microsoft", "is_current": true, ...}],
    "education": [...], "skills": [...], "certifications": [...], "languages": [...],
    "profile_images": {"profile_picture": "https://...", "cover_photo": "https://..."},
    "contact_info": {"email": "", "websites": [...], "twitter": ""}
  }
}
```

Interactive docs: `GET /docs` (Swagger UI).

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: paste li_at + JSESSIONID from a BURNER LinkedIn account
#   (DevTools -> Application -> Cookies -> www.linkedin.com)

uvicorn main:app --port 8099
```

Run tests:
```bash
pytest tests/test_client.py::test_parse_synthetic -q   # offline, no network
pytest tests/test_client.py::test_live_gate -q         # needs .env + network
```

---

## Deploy

Two options (both used the same FastAPI app):

**A. Cloudflare quick tunnel (instant public HTTPS, no DNS):**
```bash
uvicorn main:app --port 8099 &
cloudflared tunnel --url http://localhost:8099
# -> prints a https://*.trycloudflare.com URL
```

**B. Permanent subdomain (nginx + certbot):**
```nginx
# /etc/nginx/sites-available/linkedin-api
server {
  listen 443 ssl;
  server_name li-api.yourdomain.com;
  location / { proxy_pass http://127.0.0.1:8099; }
}
```
```bash
certbot --nginx -d li-api.yourdomain.com
systemctl enable --now linkedin-api   # systemd unit runs uvicorn
```

---

## Known limitations (documented, not bugs)

- **Cookies expire in 3–7 days** → 401/403. No browser automation is used, so
  there is no auto-refresh; re-login the burner in a browser to refresh.
- **Account ban risk.** Automated access violates LinkedIn ToS §8.2. Use a
  dedicated burner; keep volume low.
- **Partial data.** Email / contact info is gated and frequently empty.
  Full skills lists may be truncated.
- **Decoration schema rotation.** The `decorationId` pin (`-93`) rotates every
  4–8 weeks; re-capture the live value if the API starts returning 400/empty.
- **Datacenter IP.** Running from a cloud VM raises LinkedIn's fraud score;
  acceptable for low-volume demo use, documented as a limitation.
- **Legal.** Scraping *public* LinkedIn data is lawful under US precedent
  (hiQ v. LinkedIn), but violates LinkedIn ToS; storing EU personal data implicates
  GDPR. Do not persist PII.
