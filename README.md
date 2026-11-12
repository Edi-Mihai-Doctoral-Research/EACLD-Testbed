# EACLD-Testbed

Evidence-Adaptive Cross-Layer Diagnosis (EACLD) — Distributed Experimental Testbed.

This repository implements the EACLD distributed experimental testbed defined in technical architecture V1, maintained in the TUIAȘI research directory. The initial services are on `main`; the cumulative H1–H4 experimental operators and regression tests are on `feature/h4-experiment-runner`.

## Project status and continuation

**[PROJECT_STATUS.md](PROJECT_STATUS.md)** is the authoritative implementation status and continuation log. It records completed work, verification, the exact next component, source documents, and decisions needed to resume work in a new session. Update it whenever the implementation progresses.

## Computational experiment E0

The original E0 mathematical and computational source is maintained in the separate private repository [EACLD-Mathematical-Model](https://github.com/Edi-Mihai-Doctoral-Research/EACLD-Mathematical-Model). It contains the Bayesian engine, simulator, evaluation scripts, experiment configurations and tests, matching the source in `EACLD_E0_Experiment_2026_11_04.zip` (SHA-256: `0c495ac36ef06c5654673a6996d6478953750dd0eb414ba45eede0e1c3404454`). The full research archive, including generated data, results and figures, is maintained on the TUIAȘI Google Drive in `03 Experimente și rezultate`. This testbed reuses the E0 inference engine through the existing `core/vendor/e0/` integration.

### E0 source archive and import repair (2026-11-12)

The vendored archive `core/vendor/e0/e0_source.zip.b64` contains the original `EACLD_E0_Experimental_Package/eacld/simulator.py`, `eacld/core.py`, `eacld/__init__.py`, `config/e0_config.json`, `results/fitted_model.json`, and `tests/test_core.py`. On 12 November 2026, the original `simulator.py` was restored from `EACLD-Mathematical-Model`, correcting the missing module that caused `ModuleNotFoundError: No module named 'eacld.simulator'` during earlier GitHub Actions test collection. The existing E0 Bayesian engine `eacld/core.py` was not modified.

The archive was updated on `main` (commit `333bb956`) and `feature/h4-experiment-runner` (commit `841c96b`). On the H4 branch, `control/experiments/verify_h1_h4.sh` now extracts the archive and uses `core/vendor/e0/EACLD_E0_Experimental_Package` in `PYTHONPATH` for VM-CORE regression tests (commit `4629c76`). GitHub Actions still uses manual `workflow_dispatch`; it has not been run following these changes.

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

- NET-DATA: VMnet2, 10.60.10.0/24 — MQTT telemetry through VM-EDGE
- NET-PROBE: VMnet3, 10.60.20.0/24 — direct active verification and reference requests
- NET-CONTROL: VMnet4, 10.60.30.0/24 — authorized agent configuration and control
- NET-PLANT: VMnet5, 10.60.40.0/24 — separate reads of the shared virtual process
- ADMIN: VMnet8, NAT/DHCP — system administration

## Information access boundaries

Private intervention parameters and ground-truth data remain on VM-CONTROL and are not accessible to VM-CORE. Per-node HMAC keys are held only by VM-NODES and the verifier on VM-CORE. VM-EDGE does not possess those keys.

The existing E0 computational artifact is reused on VM-CORE through `LiveEnvironment`; `eacld/core.py` is not rewritten.

Implementation status and next steps are maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md).
