---
title: backend-language-selection
type: note
permalink: project-texttospeech/backend-language-selection
---

# Backend language selection

- [architecture] As of 2026-11-20, an unmerged TextToSpeech worktree change defaults short inputs without an explicit request language to `de-DE` via `TTS_DEFAULT_LANGUAGE`; operators can override this setting. Unsupported automatic detections fall back to `de-DE` independently of that setting. Explicit supported languages and recognized German or English detections retain precedence. When the optional classifier is unavailable, the bounded word-marker heuristic falls back to German if it recognizes neither language. See `backend/app/language.py`, `backend/app/config.py`, and the backend synthesis living specification for the current source of truth; verify integration before assuming the change is merged.
