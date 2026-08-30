# Tross Engineering Challenge — Handoff

## Status: IN PROGRESS (seeded, not deployed)

## What This Is
**Company:** Tross (ontross.com)
**Role:** Software Engineer
**Challenge:** Build a LinkedIn Profile API — reverse-engineered, no browser automation
**Deadline:** Monday, August 31, 2026 (TOMORROW)
**Submission:** https://tally.so/r/KYK6qg

## Challenge Requirements
1. Deploy API publicly over HTTPS
2. Accept LinkedIn profile URL as input
3. Return structured JSON: name, headline, location, about, experience, education, skills, certifications, languages, profile images
4. May use own LinkedIn credentials in backend
5. Submit public GitHub repo with source code
6. README with setup instructions, API docs, approach, known limitations
7. Keep credentials out of repo
8. **CRITICAL: Purely reverse-engineered — NO browser automation (Selenium/Playwright). Direct LinkedIn endpoint hits only.**

## What's Built (in this directory)
- `linkedin_scraper.py` — LinkedIn Voyager API client (reverse-engineered, requests-based, no browser)
- `main.py` — FastAPI backend with `/profile` endpoint
- `requirements.txt` — dependencies
- `.env.example` — env template for LI_AT_COOKIE
- `.gitignore`

## What's NOT Done
1. **No LinkedIn credentials yet** — need Naman's `li_at` cookie from browser
2. **Not deployed** — needs to run on VPS (port 8099) with HTTPS
3. **Not pushed to GitHub** — need to create repo
4. **Not submitted** — fill tally.so form
5. **README.md not written** — needs setup docs, API docs, approach, limitations
6. **Not tested end-to-end** — needs live li_at cookie to verify Voyager API calls work

## Architecture
```
Client → FastAPI (port 8099) → LinkedIn Voyager API → Parse included[] → Structured JSON
```

**Auth flow:**
1. Naman logs into LinkedIn in browser
2. Copies `li_at` cookie from DevTools → Application → Cookies
3. Sets as env var `LI_AT_COOKIE` on VPS
4. API uses it for all Voyager API calls

**Key endpoint:**
```
GET https://www.linkedin.com/voyager/api/identity/dash/profiles
    ?q=memberIdentity
    &memberIdentity={slug}
    &decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-93
```

**Headers:**
```
csrf-token: ajax:00000000000000000000
x-restli-protocol-version: 2.0.0
accept: application/vnd.linkedin.normalized+json+2.1
```

## Next Session Steps
1. Get li_at cookie from Naman
2. Test scraper against a real profile (e.g., satyanadella)
3. Fix any parsing issues (Voyager response format may differ from docs)
4. Write README.md
5. Deploy on VPS with HTTPS (nginx reverse proxy or direct)
6. Create GitHub repo, push code
7. Submit via tally.so
8. Verify submission went through

## Files
```
/root/tross-challenge/          (VPS — source of truth)
/home/knamant/tross-challenge/  (Flex — copy for Naman)
```

## Contact
- Tross Careers: careers@ontross.com
- Naman's email: talktonaman@duck.com
- Submission form: https://tally.so/r/KYK6qg
