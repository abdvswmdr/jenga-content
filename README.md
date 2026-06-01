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
/jenga-writer checklist  →  anti-AI-slop pass
        ↓
posts/  →  Dev.to  →  LinkedIn  →  Reddit
```

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
