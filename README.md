# EACLD-Testbed

Evidence-Adaptive Cross-Layer Diagnosis (EACLD) — Distributed Experimental Testbed.

The repository provides the seven EACLD application services on `main` and the H1–H4 experimental operators and regression tests on `feature/h4-experiment-runner`. Block B01 uses source revision `68a75fff317318296f3ada7b7e20d193f5bd04db`. The distributed testbed runs on five Ubuntu Server 26.04 LTS virtual machines hosted by Proxmox VE 9.2.2.

## Project status and continuation

**[PROJECT_STATUS.md](PROJECT_STATUS.md)** records the current implementation status, experimental verification, software locations, and technical development history.

## Computational experiment E0

The E0 mathematical and computational source is available in the separate public repository [EACLD-Mathematical-Model](https://github.com/Mihailescu-Ghiuzan-Chiper-Research/EACLD-Mathematical-Model). It contains the Bayesian engine, simulator, evaluation scripts, experiment configurations and tests, matching the source in `EACLD_E0_Experiment_2026_11_04.zip` (SHA-256: `0c495ac36ef06c5654673a6996d6478953750dd0eb414ba45eede0e1c3404454`). The full research archive, including generated data, results and figures, is maintained on the TUIAȘI Google Drive in `03 Experimente și rezultate`. This testbed reuses the E0 inference engine through the existing `core/vendor/e0/` integration.

### E0 source package and test environment

The E0 package in `core/vendor/e0/e0_source.zip.b64` contains `EACLD_E0_Experimental_Package/eacld/simulator.py`, `eacld/core.py`, `eacld/__init__.py`, `config/e0_config.json`, `results/fitted_model.json`, and `tests/test_core.py`. VM-CORE loads the Bayesian engine and calibrated model from this package.

The verification script `control/experiments/verify_h1_h4.sh` extracts the E0 archive and sets `PYTHONPATH` to `core/vendor/e0/EACLD_E0_Experimental_Package` for the VM-CORE regression tests. The GitHub Actions workflow can also be started with `workflow_dispatch`.

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
- `core/compose.yaml`, `core/services/core/{Dockerfile,requirements.txt,src/}`, `core/vendor/e0/e0_source.zip.b64`, `core/secrets/pg_password`, `core/volumes/postgres/`

Application source and Docker configurations are tracked in the repository. The E0 archive is extracted when building the VM-CORE container. VM-specific secrets and runtime volumes are provisioned for deployment.

## Communication networks

- NET-DATA: Proxmox bridge `vmbr610`, 10.60.10.0/24 — MQTT telemetry through VM-EDGE
- NET-PROBE: `vmbr620`, 10.60.20.0/24 — direct active verification and reference requests
- NET-CONTROL: `vmbr630`, 10.60.30.0/24 — authorized agent configuration and control
- NET-PLANT: `vmbr640`, 10.60.40.0/24 — separate reads of the shared virtual process
- ADMIN: `vmbr1`, VLAN 200, 10.100.200.0/24 — system administration

## Experimental verification

Experimental block B01 was executed on the five-VM testbed using the pinned source revision. Episodes H1-001, H2-001, H3-001 and H4-001 produced the expected diagnoses and traceable telemetry records. The process baseline and intervention states were restored after execution, and the consolidated regression suite passed 72 tests.

## Information access boundaries

VM-CONTROL stores intervention parameters and causal ground truth; VM-CORE processes observable telemetry and verification results. Per-node HMAC keys are held by VM-NODES and the VM-CORE verifier. VM-EDGE forwards and processes frames according to the configured G1/G2 operations.

VM-CORE integrates the E0 Bayesian policy engine (`eacld/core.py`) through the `LiveEnvironment` adapter.

Implementation status and next steps are maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md).
