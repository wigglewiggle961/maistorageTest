# Phase 1: Project Foundation & Environment Setup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 01-project-foundation-environment-setup
**Areas discussed:** Docker/Deployment, Dependency Management, Project Layout, Ollama Runtime

---

## Docker & Deployment

| Option | Description | Selected |
|--------|-------------|----------|
| Docker Compose (Ollama + app containers) | Full containerization with GPU passthrough | |
| Local dev only (no Docker) | Skip containerization entirely, focus on local machine | ✓ |

**User's choice:** Local dev only — Docker is explicitly dropped for v1.
**Notes:** User wants to focus purely on local development. This removes INFRA-03 (docker-compose.yml) and Plan 3 from Phase 1 scope entirely.

---

## Dependency Management

| Option | Description | Selected |
|--------|-------------|----------|
| `requirements.txt` | Standard pip pinned deps file | ✓ |
| `pyproject.toml` (uv/pip) | Modern Python packaging with optional uv toolchain | |

**User's choice:** `requirements.txt`
**Notes:** Simpler, widely understood, no extra tooling required.

---

## Project Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Flat `src/` layout | All source modules directly in `src/`, scripts in `scripts/` | ✓ |
| Package with `__init__.py` hierarchy | Nested sub-packages under `src/` | |
| Flat scripts only | No `src/` — all code in top-level scripts | |

**User's choice:** Flat `src/` layout
**Notes:** Keeps imports simple. All modules live at `src/module_name.py`, no nested package hierarchy needed for this project scope.

---

## Ollama Runtime

| Option | Description | Selected |
|--------|-------------|----------|
| Ollama on host machine | App connects to `http://localhost:11434` | ✓ |
| Ollama in Docker container | Requires GPU passthrough config in compose | |

**User's choice:** Host machine Ollama
**Notes:** Consistent with dropping Docker. App talks to the local Ollama process the developer already has running.

---

## Agent's Discretion

- Exact dependency versions for `requirements.txt`
- README structure and section ordering

## Deferred Ideas

- Docker Compose scaffold (INFRA-03) — explicitly deferred, belongs in v2 if ever needed
