# jenga-content

> **jenga** /ˈdʒɛŋɡə/ — Swahili: *to build*

A repository of technical articles on agentic AI, multi-model workflows, and developer tooling. Writing, reviewing, and cross-posting are done in collaboration with Claude Code and Gemini CLI.

---

## Where to Read

| Platform | Link |
|---|---|
| Dev.to | <!-- add your Dev.to profile URL --> |
| LinkedIn | <!-- add your LinkedIn profile URL --> |
| Substack | <!-- add your Substack URL --> |
| Portfolio | <!-- add your portfolio/website URL --> |

---

## Published Posts

### Agentic Workflows & Multi-Model
<!-- Add articles here as you publish them -->

### DevOps & Microservices
<!-- Kubernetes, Azure AKS, Jenkins, Istio, Terraform -->

### LLM Engineering
<!-- Prompting, agent architecture, model comparisons (Claude vs Gemini vs Qwen vs DeepSeek) -->

### Build in Public
<!-- Session logs turned into posts — real sessions, real failures -->

---

## How This Repo Works

```
_context/          ← raw AI session logs (Gemini, Claude, Qwen, DeepSeek)
    └── article-slug-source-log.md

drafts/            ← work in progress
    └── draft-title.md

posts/             ← published, crossposted
    └── article-title.md

images/covers/     ← cover images for Dev.to and social cards

scripts/           ← Dev.to crosspost automation
```

A typical article lifecycle:

```
Dev session with Gemini / Claude Code / Qwen
        ↓
/chatlog-to-article  →  _context/ log saved
        ↓
article-drafter agent  →  drafts/ outline approved → full draft
        ↓
/jenga-writer checklist  →  anti-AI-slop pass, draft: false, move to posts/
        ↓
generate cover image (scripts/generate_cover.py)
        ↓
register in schedule.json (scripts/plan_schedule.py --merge)
        ↓
dry-run crosspost (scripts/devto_crosspost.py --dry-run)
        ↓
Dev.to  →  LinkedIn  →  Reddit
```

---

## Publishing to Dev.to

**1. Generate the cover image**

```bash
python3 scripts/generate_cover.py posts/your-article-slug.md
# outputs: images/covers/your-article-slug.png
```

Or regenerate all posts missing covers:

```bash
python3 scripts/generate_cover.py --all
```

Push the cover to GitHub before posting — Dev.to loads it from the raw GitHub URL.

**2. Register the article in the schedule**

```bash
python3 scripts/plan_schedule.py \
  --start 2026-06-01 \
  --slugs "your-article-slug" \
  --merge
```

Default cadence is Tuesday/Thursday. Override with `--cadence mon,wed,fri`. For a single article you want posted today, pass today's date as `--start`.

You can also edit `scripts/schedule.json` directly — add an entry under `articles`:

```json
{
  "date": "2026-06-01",
  "file": "posts/your-article-slug.md",
  "devto": null,
  "cover_image": "https://raw.githubusercontent.com/abdvswmdr/jenga-content/main/images/covers/your-article-slug.png"
}
```

**3. Dry-run to confirm**

```bash
python3 scripts/devto_crosspost.py --status   # see what's due
python3 scripts/devto_crosspost.py --dry-run  # preview without posting
```

**4. Set your API key**

Create `scripts/.env` (never commit this file):

```
DEVTO_API_KEY=your_key_here
```

Get your key from [dev.to/settings/extensions](https://dev.to/settings/extensions) → DEV Community API Keys.

**5. Post**

```bash
python3 scripts/devto_crosspost.py
```

`schedule.json` is updated with the Dev.to URL on success.

---

## Claude Code Integration

```
~/.claude/
├── agents/
│   └── article-drafter.md     # 3-phase writer: analyze → draft → self-review
└── skills/
    ├── jenga-writer/           # Voice and tone guide
    └── chatlog-to-article/     # Session log → article pipeline

jenga-content/.claude/
└── rules/
    └── content-integrity.md   # Content integrity principle
```

---

## Tech Stack

- **Claude Code** — Writing, reviewing, crossposting
- **Gemini CLI** — Research and first-pass drafts
- **Python** + httpx + python-frontmatter — Dev.to crosspost automation
- **markdownlint-cli2** — Markdown linting

---

## License

Articles are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Code in `scripts/` is MIT.
