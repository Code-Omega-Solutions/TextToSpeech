# Private VibeVoice evaluation

This optional evaluator lives outside the production application. It adds no
production route, dependency, service setting, model download, or automatic
fallback. It evaluates only the exact candidates `VibeVoice-TTS-1.5B` and
`VibeVoice-Realtime-0.5B`; language support and availability are not inferred.

## Prepare private inputs

Create a UTF-8 JSON manifest outside the repository and restrict it to the
current user (`chmod 600 manifest.json`). It must contain:

- Five distinct sample IDs per evaluated language. Each sample needs its text,
  BCP 47 language tag, source attribution, permission status, and a reference to
  a sample-text authorization.
- A baseline configuration for each language and a separate configuration for
  each candidate being assessed. Each configuration records its exact method or
  model variant, voice, language, machine ID, availability, and applicable
  authorization IDs.
- Authorization records for sample text, voice, model, implementation, and
  dependencies. Record the terms reference, intended use, status, and review
  time for every permitted or denied use. Unresolved terms block that material.

All configurations in one run must identify the same machine. Do not include
sample texts, generated audio, credentials, or model weights in the repository.
Inspection and evaluation output must use a dedicated owner-only directory
outside the repository.

## Inspect and run

Run commands from `backend/`:

```text
uv run python -m evaluation.vibevoice.cli inspect \
  --manifest /private/path/manifest.json \
  --machine-id candidate-machine \
  --volume /private/model-volume

uv run python -m evaluation.vibevoice.cli run \
  --manifest /private/path/manifest.json \
  --output-dir /private/path/evaluation-run \
  --machine-id candidate-machine \
  --volume /private/model-volume \
  --adapter VibeVoice-TTS-1.5B=/absolute/path/to/approved-adapter \
  --approve-run
```

Inspection reads local platform, available-memory, selected-volume, and
already-installed adapter information. It does not run a model or change the
machine. An unavailable storage or memory measurement blocks generation rather
than assuming capacity. Other missing measurements and blockers are reported
explicitly. Peak memory and installed footprint remain missing unless a trusted
measurement is provided. Generation time is measured per completed sample
result.

Each `--adapter` value names one exact variant and an executable. The evaluator
starts that executable directly, without a shell, sends one JSON request on
standard input, and expects WAV bytes on standard output. The request contains
`text`, `language`, `voice`, `model_variant`, and `response_format`. Adapters
must already be installed and their implementation, dependencies, model, and
voice terms must be reviewed. The child process has a timeout, an audio-output
size limit, offline-oriented environment settings, and does not receive the
baseline API credential. The evaluator never downloads or installs an adapter.

The `--approve-run` flag authorizes only this local evaluation. It does not
authorize a download, installation, service change, or publication. The
baseline uses the existing authenticated `POST /v1/audio/speech` endpoint and
reads its credential from the backend's protected `TTS_API_KEY` or
`TTS_API_KEY_FILE` settings. If the baseline or a candidate is unavailable, the
report records the blocker instead of substituting another method.

## Review the private report

The report and audio are saved under the output directory with owner-only
permissions. Start the loopback-only review server:

```text
uv run python -m evaluation.vibevoice.cli serve \
  --report /private/path/evaluation-run/report.json
```

Open `http://127.0.0.1:8000/listening-review` for paired playback and
per-sample ratings, or `http://127.0.0.1:8000/results-summary` for individual
results, averages, observations, resource evidence, missing-data reasons, and
the product-owner decision. If port 8000 is occupied, choose another with
`--port`. There is no automatic score threshold.

The pages and API are local to the selected run. The server binds to
`127.0.0.1`, requires same-origin requests and a run-scoped session token for
report operations, and resolves audio only by completed result ID. Keep the
output directory private and stop the server when review is finished.

## Disable or remove

To disable the prototype, do not invoke its module. To remove it, delete
`backend/evaluation/vibevoice/` and the evaluator-only tests
`backend/tests/test_evaluation.py`,
`backend/tests/test_evaluation_comparison.py`,
`backend/tests/test_evaluation_inspection.py`, and
`backend/tests/test_evaluation_web.py`. No production speech code or service
configuration needs to change.
