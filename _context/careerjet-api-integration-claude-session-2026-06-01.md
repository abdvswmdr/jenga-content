# Raw session context — Careerjet API integration
# Date: 2026-06-01
# Source: Claude Code session in sakamboka/

## What happened

Building a job discovery pipeline for SakaMboka (AI resume tool targeting Kenya).
Google AI Mode (Gemini) had recommended Careerjet as a "public API — no scraping, structured data."

Claude Code implemented it based on that description, using the old unofficial endpoint:
- `http://public.api.careerjet.net/search`
- Used `affid` param (affiliate ID) as auth, set to "sakamboka-ke" as a fallback string
- No actual authentication
- Used `urllib.request` instead of httpx

User then registered on Careerjet's publisher portal and came back with the actual docs.

## What the actual API looks like

- Endpoint: `https://search.api.careerjet.net/v4/query`
- Auth: HTTP Basic auth — API key as username, empty string as password → base64 encoded
- Required params: `user_ip`, `user_agent` (by the API spec — "IP of the user whose action triggered the call")
- Required header: `Referer` (the publisher's site URL)
- IP whitelisting: must register the server IP in the publisher dashboard
- API key: obtained from publisher registration, tied to a specific domain (sakamboka.co.ke in this case)

## The gap

"Public" in Careerjet's context means "available to registered publishers without approval gating" — 
not "no authentication required." There's a registration step, IP whitelisting, and Basic auth on every request.

The old endpoint (public.api.careerjet.net) was a v2 affiliate widget API that did work without auth
for display purposes — affid tracked click revenue. The v4 API is the proper search API for publishers
building job search into their sites.

## The pipeline use case problem

The API was designed for user-facing job search (someone types "Software Engineer" and clicks Search).
Hence `user_ip` and `user_agent` are required — Careerjet wants to know real user behavior for analytics.

In a batch pipeline (no real user, runs nightly), there is no actual user IP or agent.
Fix: pass the VPS outbound IP (178.162.244.63) as user_ip and a standard Chrome UA string.
The API spec says "user whose action triggered the call" — the nightly cron is the trigger, server is the "user."

## Files changed

- `applypilot/discovery/careerjet.py` — complete rewrite
- `pyproject.toml` — playwright-stealth added (different change in same session)
- `applypilot/config/sites.yaml` — marker entry for Careerjet
- `applypilot/pipeline.py` — wired as scraper #7
