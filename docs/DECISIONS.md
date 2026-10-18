# DECISIONS — Register of Choices the Agent Must Not Invent

Each entry has a **default** (use it unless a human changes it), the **change trigger**, and the **impact**.
The agent may not flip a decision on its own; it writes `DECISION NEEDED` and stops.

---

| ID | Decision | Default | Change requires | Impact if wrong |
|---|---|---|---|---|
| **D-01** | Orphaned Flutter screens (`home`, `record`, `review_edit`, `preview_qa`, `storefronts`) | **Delete** them and their exclusive widgets | Human sign-off | Keeping them misrepresents the app; reviving them is ~1,150 lines to maintain. |
| **D-02** | Published URL scheme | **(a)** `https://{domain}/storefronts/{version_id}/index.html` — URL matches the S3 key | Human sign-off | (b) shorter URLs need a CloudFront Function; without it the URL 404s. |
| **D-03** | Auth scope in phase 1 | **API key** on `/v1/publish` and `/v1/layout/scrape`; rate limits everywhere | Security review | Full user auth is out of scope; claiming it is a false claim. |
| **D-04** | Metric thresholds | **Measure first.** Set WER/F1/latency thresholds after the first run; record actual value beside target | Human sign-off | Inventing a threshold is a fabricated result. |
| **D-05** | AWS actions | Agent runs `terraform plan` only. **No `apply`.** | Human executes apply | Unattended infra changes can create public buckets. |
| **D-06** | Component-library approval | Harvester writes `PENDING`; only human/CI review sets `APPROVED`; duplicates marked `DUPLICATE` | Human sign-off | 59 scraper-approved entries include duplicates and a "JavaScript is disabled" capture. |
| **D-07** | Repair strategy | **Deterministic BeautifulSoup fixers first.** LLM only for a single node, optional, behind a flag | Human sign-off | Whole-page LLM repair corrupts pages. |
| **D-08** | Scraping feature in deployment | Keep, but gate behind `X-Internal-Token` | Human sign-off | An open fetcher is an SSRF proxy. |
| **D-09** | Persistence | **SQLite** for QA history and the learned patch store (stdlib `sqlite3`); no Postgres/Redis | Human sign-off | Postgres is designed-only; adding it expands scope by days. |
| **D-10** | ASR mode default | `ASR_MODE=live`; simulator requires explicit `ASR_MODE=simulator` | Human sign-off | A silent simulator fabricates menu content. |
| **D-11** | Language handling | English only this semester; `language_detect` deleted or documented as unused | Human sign-off | Claiming multilingual is false. |
| **D-12** | API surface for `invalid_fields` | Change to documented `[{field, reason}]` (contract wins) | Human sign-off | Changing the contract instead would break the documented API. |
| **D-13** | `shop_id` | Remove from requests if unused, or persist it (D-09) | Human sign-off | An ignored field is misleading. |
| **D-14** | `apps/web` | **Delete** the four empty pages and 0-byte Dockerfile | Human sign-off | 0-byte files imply a frontend that does not exist. |
| **D-15** | `opencode.json` | Remove from the repository | Human sign-off | Local model-router config, not project source. |
| **D-16** | `scrapy/` | **Never commit.** Remove from the working tree or add to `.gitignore` (already ignored as a nested repo is not automatic — add explicitly) | Human sign-off | 42 MB nested clone with its own `.git`. |
| **D-17** | Binary artefacts (`docs.zip`, `.docx`, `.pptx`, `.pdf`, `.xlsx`) | Keep out of git; attach to the submission separately | Human sign-off | A 50 MB blob is permanent in history. |
| **D-18** | Rate-limit values | NLP 30/min, layout 60/min, QA 10/min, scrape 5/min, publish 5/min, ASR 10/min | Human sign-off | Too tight breaks the demo; too loose protects nothing. |
| **D-19** | `passed` definition | **No critical violations** | Human sign-off | "Zero violations at all viewports" may never pass on a real page. |
| **D-20** | CI scope | Lint + unit + contract on every PR; live tests nightly/manual | Human sign-off | Live tests burn Groq quota. |

---

## How to raise a new decision

Append a row:

```
| **D-XX** | <question> | <recommended default> | <who must approve> | <impact> |
```

and stop work on that step. Do not implement a guess.
