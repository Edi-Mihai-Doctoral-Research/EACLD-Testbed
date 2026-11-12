# VM-CORE — distributed EACLD diagnosis

VM-CORE implements authenticated MQTT ingestion, persistent anti-replay checking, active evidence acquisition, the original E0 Bayesian policy engine, and PostgreSQL 16 persistence, following technical architecture V1.

## Runtime flow

- The core subscribes exclusively to MQTT accepted/+ on VM-EDGE (10.60.10.14:1883). It never subscribes to raw/+ or transit/g1/+.
- ingest.py stores accepted-topic payloads with their authentication and freshness classifications. verifier.py uses node/version HMAC keys available only on VM-NODES and VM-CORE. sequence_registry.py persists the last authenticated sequence per node/boot identifier. Invalidly authenticated frames cannot advance the high watermark.
- live_env.py implements the original E0 LiveEnvironment public state and execute(action) method. message_verify and sequence_check return the stored checks; reference_read directly reads VM-REFERENCE at 10.60.20.13:8201; node_challenge directly requests VM-NODES at 10.60.20.12:8202 and validates its nonce and HMAC.
- runner.py loads the unchanged E0 PolicyEngine, configuration and fitted model. Policy B6_EACLD selects actual checks, not synthetic outcomes. Returned latency is elapsed wall-clock time, bytes represent observed application payload sizes, and costs are the configured nominal E0 costs.
- core.py provides the source-restricted NET-CONTROL interface on 10.60.30.15:8300. Neither private cause labels nor intervention schedules are exposed to the core.

The curated source archive `vendor/e0/e0_source.zip.b64` contains six original E0 files under `EACLD_E0_Experimental_Package/`: `eacld/__init__.py`, `eacld/core.py`, `eacld/simulator.py`, `config/e0_config.json`, `results/fitted_model.json`, and `tests/test_core.py`. The original `eacld/simulator.py` was restored from `EACLD-Mathematical-Model` on 2026-11-12 (main: `333bb956`; `feature/h4-experiment-runner`: `841c96b`), correcting the earlier missing-module error in E0 test collection. The original E0 Bayesian engine `eacld/core.py` remains unchanged. The archive does not include private ground truth or synthetic potential-outcome datasets. The Docker build verifies original `core.py` SHA-256: `cedddf154553162a4bda1e12fc48045162af0918ffd975a001141ae2e4f05f58`. The full original ZIP stored on TUIAȘI Drive has SHA-256: `0c495ac36ef06c5654673a6996d6478953750dd0eb414ba45eede0e1c3404454`.

## Explicit diagnosis API

GET /healthz reports readiness after the broker acknowledges the accepted/+ subscription. The only operation for a diagnosis is POST /v1/diagnose on 10.60.30.15:8300, restricted to VM-CONTROL (10.60.30.10).

Example JSON body (illustrative values, not experimental parameters):

    {
      "node_id": 12,
      "episode_id": "operator-assigned-id",
      "block_id": "operator-assigned-block",
      "mode": "nominal",
      "baseline_temperature_mC": 22000,
      "high_delta_mC": 3000
    }

The operating mode (nominal or degraded) and temperature baseline/threshold must be provided explicitly. By default the most recent accepted telemetry is used. An optional
`expected_telemetry_id` protects H1/H2 against a changed latest message
(HTTP 409). For H3, optional `selected_telemetry_id` selects an exact
previously persisted message even if later telemetry has arrived.
These two optional fields are mutually exclusive.
The E0 engine chooses verification actions under its established finite-horizon policy. The response and persisted diagnosis contain only observable results, posterior probabilities, selected checks, costs, latency and risk. The request never accepts a cause label or private ground truth.

MQTT receipt does not automatically open a new experiment episode. VM-CONTROL decides when to invoke the diagnostic run.

## Deployment

Check out the complete repository at /opt/eacld on VM-CORE. Provision three files under /opt/eacld/core/secrets:

- node_keys.json: the same per-node/key-version hexadecimal keyring as VM-NODES;
- mqtt_password: broker password of the core principal;
- pg_password: password of the PostgreSQL eacld user.

Secrets are excluded from Git and mounted read-only. PostgreSQL runs only on the Docker-internal network; no PostgreSQL host TCP port is published. Do not mount private ground-truth data on this VM.

VM-CORE has NET-DATA 10.60.10.15, NET-PROBE 10.60.20.15 and NET-CONTROL 10.60.30.15 (plus the separate administration network), per V1.

    cd /opt/eacld/core
    docker compose up --build -d

## Verification

core/tests/test_core_service.py contains unit and API tests for HMAC, keyring, topic validation, direct probes, nonce validation, E0 inference integration, MQTT callback handling and source-restricted control. The original nine E0 mathematical core tests are also retained. The main-branch GitHub workflow contains both suites. It restores the E0 archive and imports the package through `core/vendor/e0/EACLD_E0_Experimental_Package`. The earlier CI `ModuleNotFoundError: No module named 'eacld.simulator'` was caused by the omitted archived module and was addressed by the 2026-11-12 source-package update. GitHub Actions remains manually triggered. The consolidated H1–H4 verification script on `feature/h4-experiment-runner` now extracts the same archive and uses the same package path (`4629c76`).

These tests do not establish deployment against live Mosquitto, PostgreSQL, Docker or the five-VM topology.


## Operator evidence API (H1–H3)

VM-CONTROL (10.60.30.10) alone may access the following NET-CONTROL
routes. No additional ports or information channels are introduced.

- `GET /v1/telemetry/latest?node_id=1`: the newest accepted frame for
  that node, including its stable database ID, observable decoded values,
  raw frame hexadecimal bytes, HMAC status and freshness classification.
- `GET /v1/telemetry/match?node_id=1&after_id=<id>&frame_hex=<188-lowercase-hex>`:
  the earliest exact 94-byte match after a pre-intervention telemetry
  watermark. This avoids losing the single mutated H3 frame when a newer
  normal frame is received.
- `POST /v1/diagnose`: original six research fields plus either
  `expected_telemetry_id` (latest-record guard) or
  `selected_telemetry_id` (exact persisted record), never both.
- `GET /v1/diagnosis?episode_id=...`: the persisted diagnosis with
  the exact frame and observations used by the original E0 engine.

H3 expects an invalid HMAC and unavailable sequence classification for
the modified frame. PostgreSQL retains such received frames, but an
invalid frame cannot advance the authenticated sequence watermark. The
private mutation action and original pre-mutation frame are recorded
by VM-CONTROL from G2, not inferred inside VM-CORE.

Focused tests are in `core/tests/test_operator_api.py` and
`core/tests/test_h3_core_selection.py`.


## H4 authenticated replay classification

The H4 operator reuses `GET /v1/telemetry/match`,
`POST /v1/diagnose` with `selected_telemetry_id`, and the persisted
diagnosis-readback endpoint introduced for H1–H3. H4 requires no new
VM-CORE API or change to the original E0 policy engine.

For a retransmitted, previously accepted 94-byte frame, the verifier
records `mac_status=valid` because its signed bytes are unchanged.
The persisted sequence watermark produces `sequence_status=stale`
once the original and a strictly newer message have already been
accepted for that node and boot. The H4 runner selects this exact
stored record for B6 inference; later normal traffic cannot silently
replace the diagnostic input.

Focused tests are in `core/tests/test_h4_replay_selection.py`.
