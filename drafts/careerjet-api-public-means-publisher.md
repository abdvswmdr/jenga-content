---
title: "\"Public API\" Doesn't Mean What I Thought It Meant"
description: "I implemented the Careerjet job search API before reading the docs. Here's what I got wrong and what the v4 API actually looks like."
date: 2026-06-01
tags: [api, python, webdev, career]
draft: true
---

I was integrating a job board API into a side project. An AI assistant I'd been chatting with had flagged Careerjet as a good option — structured data, Kenya support, and "a public API, so no scraping needed."

That last part stuck with me: *public API*. No auth dance, no approval process. I'd just call it.

So I did. Before reading the documentation.

---

## What I Built First

The old Careerjet affiliate API (`public.api.careerjet.net/search`) actually exists and does respond to unauthenticated requests. You pass an `affid` (affiliate ID) as a query param, which was originally used for revenue tracking on partner widgets. I set mine to a placeholder string and moved on.

```python
params = urlencode({
    "keywords": title,
    "location": "Kenya",
    "locale_code": "en_KE",
    "affid": "my-placeholder-affid",
    "pagesize": 100,
})
url = f"http://public.api.careerjet.net/search?{params}"
```

It returned JSON. I wrote the parser. I moved on.

This would have silently failed the first time it ran against any real load — or returned results that were never attributed to my site, meaning any revenue-sharing arrangement would be untracked. But worse: I wasn't using the actual API they want publishers to use.

---

## Registering for the Real Thing

Out of curiosity I signed up on Careerjet's publisher portal. What came back was not what I expected for a "public API":

- An API key tied to my registered domain
- A page asking me to whitelist my server's IP address — mandatory, not optional
- Basic auth on every request: the key as the username, an empty string as the password

The endpoint had also changed: `https://search.api.careerjet.net/v4/query`.

So "public" here means *available to any publisher who registers* — not *unauthenticated*. The distinction matters because I'd written an integration that would have 403'd the moment Careerjet migrated the old endpoint or tightened auth requirements.

---

## What the v4 API Actually Needs

Here's the corrected implementation:

```python
import base64
import urllib.request
import json
from urllib.parse import urlencode

API_URL = "https://search.api.careerjet.net/v4/query"

def fetch_jobs(keywords: str, location: str, api_key: str, user_ip: str) -> dict:
    params = urlencode({
        "locale_code": "en_KE",
        "keywords": keywords,
        "location": location,
        "sort": "date",
        "page_size": 100,
        "user_ip": user_ip,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    })

    credentials = base64.b64encode(f"{api_key}:".encode()).decode()

    req = urllib.request.Request(f"{API_URL}?{params}")
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Referer", "https://your-site.com/jobs/")

    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())
```

Three things I hadn't accounted for:

**1. Basic auth with an empty password**

The format is `base64(api_key + ":")`. Standard HTTP Basic auth — username is the key, password is blank. Not obvious unless you look at the docs or the curl example.

**2. `user_ip` and `user_agent` are required params**

This one is interesting. The API was designed for publishers embedding job search on their website, so a real user is typing the query. Careerjet wants the user's IP and browser agent for analytics, not yours.

For a batch pipeline — no browser, no user, runs on a cron — what do you pass? The spec says "the IP of the user whose action triggered the API call." The nightly job is the trigger. I pass the server's outbound IP. It works.

**3. IP whitelisting is mandatory**

Before any request succeeds, you declare which IP addresses are allowed to call the API. In the publisher dashboard, there's a text box for up to 8 addresses. Your server IP must be in there or you get a 403 regardless of auth headers.

This is a reasonable security measure — it ties the API key to specific infrastructure. It also means if your server IP changes (new VPS, new cloud instance), you have to update the dashboard before your integration breaks.

---

## The Response Shape

On success you get `type: "JOBS"` with a `jobs` array. Each job has:

```json
{
  "title": "Software Engineer",
  "company": "Some Company",
  "locations": "Nairobi",
  "date": "Mon, 01 Jun 2026 08:00:00 GMT",
  "description": "Short excerpt...",
  "salary": "KES 80,000 - 120,000 per month",
  "url": "https://jobviewtrack.com/v2/..."
}
```

On a location disambiguation case — when Careerjet can't resolve your `location` param to a single place — you get `type: "LOCATIONS"` with a list of options. Worth handling:

```python
data = fetch_jobs(...)
if data.get("type") != "JOBS":
    # Careerjet returned a LOCATIONS disambiguation response
    # Log it and continue; "Kenya" or "Nairobi" should resolve cleanly
    return []
```

---

## What I'd Do Differently

Read the documentation before writing the first line of integration code.

This sounds obvious and it is, but there's a particular failure mode when you're using AI assistants as a research shortcut: you get a confident summary of how something works, and that summary is out of date, or applies to a different version, or conflates "publicly available to publishers" with "no credentials needed."

In this case the old API endpoint worked well enough to feel correct. That's the worst kind of wrong — it doesn't fail immediately, it fails later, under different conditions, in ways that are harder to trace.

The registration process for Careerjet's publisher API takes about ten minutes. The documentation is clear. I could have read it first.

---

The integration works now. Careerjet has solid Kenya coverage and the structured salary data (`salary_currency_code: "KES"`) is a nice bonus over scraping salary strings out of job descriptions. If you're building anything that aggregates East African job listings, it's worth registering.

Just read the docs first.
