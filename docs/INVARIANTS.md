# INVARIANTS — What the Agent May Not Change

> Read this before any code change. If a task appears to require violating an invariant, **stop and write a
> `DECISION NEEDED` note** in `docs/DECISIONS.md` instead of proceeding.
> Invariant IDs are stable; reference them in PR descriptions (`Closes: I-07`).

---

## A. Architecture

| ID | Invariant | Why |
|---|---|---|
| **I-A1** | Five services exist: `asr-service`, `nlp-service`, `layout-service`, `qa-service`, `publish-service`. No merges, no splits. | The five-stage mapping is the project's scope contract (audit §0). |
| **I-A2** | Ports are fixed: ASR 8001, NLP 8002, layout 8003, QA 8004, publish 8005. | Compose, the Flutter client, the visualizer and the report all reference them. |
| **I-A3** | Route paths are fixed: `POST /v1/asr/transcribe`, `POST /v1/nlp/extract`, `POST /v1/layout/generate`, `POST /v1/layout/scrape`, `POST /v1/qa/run`, `POST /v1/publish`, `GET /health` (all services). | `api_contracts.md`; changing a path breaks the client and the report. |
| **I-A4** | `packages/schemas/entity_types.py` is the **single source of truth** for `StorefrontSpec`. JSON Schema and TypeScript are generated from it, never hand-edited. | NFR-4. Hand-editing is how the current drift happened. |
| **I-A5** | Every service calls Groq through **one** shared client (`packages/common_utils/groq_client.py` once A1 lands). No new direct `groq`/`httpx` calls to Groq. | Three independent paths exist today; a model change must happen once. |
| **I-A6** | Services must not import each other. Cross-service communication is HTTP only. | Independent deployability (NFR-3). |
| **I-A7** | No new heavy dependencies (torch, transformers, faiss, codebert, transformers, sentence-transformers) without a recorded decision. | Deployment size and the "no local GPU" constraint. |
| **I-A8** | `data/constraint-rules/*.json` and `data/component-library/**` are read-only at runtime. Services never write to them. | State ownership; the library is an input, not a cache. |

## B. Test integrity

| ID | Invariant | Why |
|---|---|---|
| **I-T1** | An existing assertion may not be deleted, weakened, skipped, or `xfail`-ed to make a proof pass. Fix the code or record a `DECISION NEEDED`. | The audit found tests that were already softened (`has_components(nonexistent)`, the tautological render check). |
| **I-T2** | Fixtures under `data/seed/` may be **added to**, never edited to make a test pass. If a fixture is wrong, add a new one. | Editing fixtures hides regressions. |
| **I-T3** | A threshold (WER, F1, latency, WCAG pass rate) is set **only after** the first real measurement, and the measured value is written next to it. | Targets must not be quoted as results. |
| **I-T4** | Tests must pass offline unless explicitly marked `@pytest.mark.live`; live tests are skipped when the key is absent, and the skip reason is printed. | The demo must work without network. |
| **I-T5** | Every Proof command in `docs/proofs.json` must exit non-zero on failure. A proof that cannot fail is not a proof. | Anti-hallucination: "it printed OK" is not evidence. |

## C. Security

| ID | Invariant | Why |
|---|---|---|
| **I-S1** | No secret, key, token, or password may be written to a tracked file. `.env` stays ignored; never `git add -f`. | Keys were found on disk. |
| **I-S2** | Every HTML sink escapes by default: Jinja `autoescape=True`, client fallbacks use `HtmlEscape`, JSON-LD escapes `</`. | Stored XSS is the audit's highest finding. |
| **I-S3** | No user-controlled string reaches a filesystem path, S3 key, or URL path without `safe_version_id` validation. | Path traversal in QA and publish. |
| **I-S4** | No new endpoint that fetches a caller-supplied URL without an allow-list and private-IP rejection. | `/scrape` SSRF. |
| **I-S5** | No new mutating endpoint without a rate limit; no new expensive endpoint without a body-size cap. | Shared Groq quota and memory exhaustion. |
| **I-S6** | Error responses must not echo stack traces, child-process stderr, or raw exception text. | Information disclosure. |
| **I-S7** | Containers run as non-root. | Container hardening. |

## D. Claims and documentation

| ID | Invariant | Why |
|---|---|---|
| **I-D1** | No document may claim a metric that has no runnable script and a recorded output. | `testing.md` targets were presented as results. |
| **I-D2** | No document may describe a feature as implemented when `docs/proofs.json` has no passing proof for it. | `UPDATES.md` claimed template switching that never existed. |
| **I-D3** | Documentation edits are allowed **only** in steps `D1`–`D7`. Code PRs may not touch `docs/*.md` except the changelog and state files. | Prevents the agent from "fixing" docs to match unfinished code. |
| **I-D4** | The honest-limitations list in `REMEDIATION_PLAN_TO_A_PLUS.md` §15 must remain true after every PR. If a change makes one of them false, update the list — do not delete it silently. | Keeps the A+ claim defensible. |

## E. Process

| ID | Invariant | Why |
|---|---|---|
| **I-P1** | One PR/step group at a time. Do not start step *n+1* until the verifier reports *n* green. | The dependency graph is real. |
| **I-P2** | A step is "done" only when `python scripts/verify_step.py <ID>` exits 0 **and** its output is pasted into the PR. | Proof over prose. |
| **I-P3** | The agent may modify only the files listed in that step's `allowed_files`. Any other diff must be reverted. | Scope control. |
| **I-P4** | No `git push`, no `terraform apply`, no cloud mutation, no key rotation by the agent. These are human actions. | Outward-facing changes need a person. |
| **I-P5** | If a proof fails twice for the same reason, stop and report; do not "try a different approach" that changes the design. | Prevents drift and creative workarounds. |
| **I-P6** | Never delete `scrapy/`, `docs/papers/`, `.env`, `data/constraint-rules/`, or any `fixture-*.html`. | Irreplaceable or scope-defining inputs. |

---

## Emergency stop

Stop immediately and report if any of these happen:

1. A proof requires network access that is not available.
2. A fix would change a public request/response shape (I-A3).
3. Two invariants conflict.
4. A test that previously passed now fails and the cause is not understood.
5. You are about to modify a file outside `allowed_files`.
6. You catch yourself writing "this should work" without a run.
