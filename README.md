# EACLD-Testbed

Evidence-Adaptive Cross-Layer Diagnosis (EACLD) — Distributed Experimental Testbed.

This repository contains the initial implementation structure defined in the EACLD experimental testbed technical architecture specification (V1), maintained in the TUIAȘI research directory.

## Project status and continuation

**[PROJECT_STATUS.md](PROJECT_STATUS.md)** is the authoritative implementation status and continuation log. It records completed work, verification, the exact next component, source documents, and decisions needed to resume work in a new session. Update it whenever the implementation progresses.

## Computational experiment E0

The original E0 computational source is maintained in [`EACLD-E0/`](EACLD-E0/): Bayesian engine, simulator, evaluation, experiment runner, report generator, configurations, and tests. These source files are copied without modification from `EACLD_E0_Experiment_2026_11_04.zip` (SHA-256: `0c495ac36ef06c5654673a6996d6478953750dd0eb414ba45eede0e1c3404454`). The full research archive, with generated data, results and figures, is maintained on the TUIAȘI Google Drive in `03 Experimente și rezultate`. The existing `core/vendor/e0/` integration is unchanged.

## Virtual machine allocation

| Virtual machine | Repository directory | Services |
| --- | --- | --- |
| VM-CONTROL | `control/` | `eacld-control` |
| VM-NODES | `nodes/` | `eacld-nodes` |
| VM-REFERENCE | `reference/` | `eacld-reference` |
| VM-EDGE | `edge/` | `eacld-g1`, `eacld-g2`, `eacld-edge-control` |
| VM-CORE | `core/` | `eacld-core`; reused E0 Bayesian inference engine |

Each virtual machine has a separate Docker Compose project deployed under `/opt/eacld/<directory>/`.

## Deployment directory structure

- `control/compose.yaml`, `control/services/control/{Dockerfile,requirements.txt,src/}`
- `nodes/compose.yaml`, `nodes/services/nodes/{Dockerfile,requirements.txt,src/}`
- `reference/compose.yaml`, `reference/services/reference/{Dockerfile,requirements.txt,src/}`
- `edge/compose.yaml`, `edge/services/{g1,g2,edge-control}/{Dockerfile,requirements.txt,src/}`, `edge/config/{mosquitto.conf,acl,passwd}`, `edge/volumes/mosquitto/`
- `core/compose.yaml`, `core/services/core/{Dockerfile,requirements.txt,src/}`, `core/vendor/e0/{eacld/core.py,config/e0_config.json,results/fitted_model.json}`, `core/secrets/pg_password`, `core/volumes/postgres/`

These paths describe the planned deployment structure. Application source files, Docker configurations, and runtime configuration files will be added during implementation. Empty directories are currently represented by `.gitkeep` files.

## Communication networks

- NET-DATA: VMnet2, 10.60.10.0/24 — MQTT telemetry through VM-EDGE
- NET-PROBE: VMnet3, 10.60.20.0/24 — direct active verification and reference requests
- NET-CONTROL: VMnet4, 10.60.30.0/24 — authorized agent configuration and control
- NET-PLANT: VMnet5, 10.60.40.0/24 — separate reads of the shared virtual process
- ADMIN: VMnet8, NAT/DHCP — system administration

## Information access boundaries

Private intervention parameters and ground-truth data remain on VM-CONTROL and are not accessible to VM-CORE. Per-node HMAC keys are held only by VM-NODES and the verifier on VM-CORE. VM-EDGE does not possess those keys.

The existing E0 computational artifact is reused on VM-CORE through `LiveEnvironment`; `eacld/core.py` is not rewritten.

Implementation status and next steps are maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md).
