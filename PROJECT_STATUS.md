# EACLD-Testbed — Project Status and Continuation Log

**Last updated:** 2026-11-16  
**Repository:** Mihailescu-Ghiuzan-Chiper-Research/EACLD-Testbed  
**Visibility:** Public  
**Central status branch:** main  
**Implementation checkpoint:** Seven distributed services on main; H1–H4 experiment runners and regression tests on feature/h4-experiment-runner  
**Experimental branch:** feature/h4-experiment-runner (cumulative H1–H4 implementation)  
**Current phase:** Five-VM Proxmox testbed deployed; block B01 executed successfully for H1–H4; all four episodes recorded and the consolidated regression suite passed 72 tests  
**Next software task:** Evaluate the B01 evidence and conduct additional experimental blocks according to the protocol  
**Next infrastructure task:** Maintain the configured five-VM testbed for subsequent experimental runs

This document records the current implementation, verified experiments, and chronological work log. The `main` branch contains the initial distributed services, while `feature/h4-experiment-runner` contains the cumulative H1–H4 experimental implementation. Architecture V1 defines the original technical contracts.

## 1. Current implementation status

| Area | Location | Status | Verification |
| --- | --- | --- | --- |
| Repository layout | control/, nodes/, reference/, edge/, core/ | Created | Directory layout aligned with architecture V1 |
| Original E0 computational source | EACLD-Mathematical-Model (separate public repository) | Imported and verified | 14 original source, configuration, test and documentation files; source tree identical to archived E0 source |
| Shared binary frame and HMAC-SHA256 | shared/eacld_contracts/frame.py | Implemented | 12 shared-contract tests passed |
| MQTT topic and access definitions | shared/eacld_contracts/topics.py | Implemented | Included in shared-contract tests |
| HTTP / LiveEnvironment contracts | shared/eacld_contracts/interfaces.py | Defined | Included in shared-contract tests |
| eacld-control / VM-CONTROL | control/services/control/ | Deployed in B01 | 12 local unit tests passed; distributed process and experiment control exercised in B01 |
| eacld-nodes / VM-NODES | nodes/services/nodes/ | Deployed in B01 | 21 local unit/API tests passed; authenticated telemetry and node-bias control exercised in B01 |
| eacld-reference / VM-REFERENCE | reference/services/reference/ | Deployed in B01 | 19 local unit/API tests passed; reference acquisition service included in five-VM execution |
| eacld-g1 / VM-EDGE | edge/services/g1/ | Deployed in B01 | 19 local unit/configuration tests passed; MQTT forwarding exercised in the distributed H1–H4 sequence |
| eacld-g2 / VM-EDGE | edge/services/g2/ | Deployed in B01 | 19 local unit/configuration tests passed; controlled mutation and replay exercised in H3/H4 |
| eacld-edge-control / VM-EDGE | edge/services/edge-control/ | Deployed in B01 | 8 unit/API tests committed; G2 intervention control and cleanup exercised in the distributed execution |
| eacld-core / VM-CORE | core/services/core/ | Deployed in B01 | 9 service tests committed; E0 core 9/9 local tests passed; persisted H1–H4 diagnoses recorded in B01 |
| E0 Bayesian engine | core/vendor/e0/e0_source.zip.b64 | Integrated through `LiveEnvironment` | E0 source package includes `eacld/core.py`, `eacld/simulator.py`, configuration, fitted model and core tests; 9/9 original tests passed locally |
| H1 — process intervention | control/experiments/h1_run.py; restricted VM-CORE telemetry/diagnosis API | Committed on feature/h1-experiment-runner; inherited by H2/H3 branches | Operator and API unit tests added; baseline, injected state and selected diagnostic frame recorded |
| H2 — virtual sensor measurement bias | nodes/services/nodes/src/nodes.py; control/experiments/h2_run.py | Committed on feature/h2-experiment-runner; inherited by H3 branch | Four local runner tests recorded as passed; bias API tests and automatic restoration implemented |
| H3 — G2 telemetry mutation | edge/services/g2/src/g2.py; edge/services/edge-control/src/agent.py; control/experiments/h3_run.py; VM-CORE frame selection | Committed on feature/h3-experiment-runner | Tests added for G2 mutation evidence, exact VM-CORE frame selection and operator cleanup |
| H4 — authentic telemetry replay | edge/services/g2/src/g2.py; edge/services/edge-control/src/agent.py; control/experiments/h4_run.py; VM-CORE sequence registry and exact record selection | Committed on feature/h4-experiment-runner | Tests added for bounded frame capture, authentic stale replay, exact selected diagnosis and cleanup |
| H1–H4 compatibility | control/tests/test_experiment_compatibility.py; control/experiments/verify_h1_h4.sh | Implemented and verified on feature/h4-experiment-runner | Consolidated runner loads the E0 package and VM-CORE Python path; 72 regression tests passed in B01 |
| Distributed VM deployment | Five Proxmox VE 9.2.2 virtual machines, Ubuntu Server 26.04 LTS | Deployed and tested | Block B01 executed H1–H4 across five VMs, with four recorded episode manifests |
| Regression verification | `control/experiments/verify_h1_h4.sh` | 72 tests passed | H1–H4 operator, gateway, node and core regression tests; manual GitHub Actions trigger available |


## 2. Distributed experimental verification: block B01

Block `B01` exercised the five-VM testbed using the pinned source snapshot `feature/h4-experiment-runner`, commit `68a75fff317318296f3ada7b7e20d193f5bd04db`. All four episode manifests were recorded, with the diagnostic telemetry IDs matching their persisted VM-CORE records.

| Episode | Observed evidence | EACLD diagnosis |
| --- | --- | --- |
| `H1-001` | Process and authenticated fresh telemetry: 28,912 m°C | H1 |
| `H2-001` | Process: 22,000 m°C; authenticated fresh biased telemetry: 28,912 m°C | H2 |
| `H3-001` | Modified frame after authentication; invalid HMAC, sequence unavailable | H3 |
| `H4-001` | Authentic retransmitted frame; valid HMAC, stale sequence | H4 |

The node bias was restored to zero, G2 intervention states were cleared, and the virtual process returned to 22,000 m°C. The consolidated regression suite passed 72 tests. The four episode records were packaged in `EACLD-B01-results.tar.gz`.

## 3. VM-EDGE and VM-CORE runtime services

**eacld-edge-control / VM-EDGE.** The source-restricted HTTP agent listens on 10.60.30.14:8300 (NET-CONTROL) and authorizes only VM-CONTROL at 10.60.30.10 for intervention requests. G2 has a private Unix-domain command socket shared with the agent through a dedicated Docker volume. VM-CONTROL selects and schedules experimental scenarios through explicit G2 mutate, replay and clear commands. Eight local unit/API tests are committed, and G2 intervention control was exercised during B01. The edge-control API contract is an implementation-level extension to the V1 health endpoint.

**eacld-core / VM-CORE.** Core subscribes only to accepted/+ using the core MQTT principal, parses the original 94-byte frame contract, validates HMAC against VM-CORE-only node keys and persists anti-replay state and received telemetry in internal PostgreSQL 16. The packaged E0 computational source, fitted model and configuration are loaded by the VM-CORE container. The `LiveEnvironment` adapter executes four physical and security verification actions and returns their observed outcomes, latency, communication volume and configured costs. The explicit diagnosis endpoint on VM-CORE NET-CONTROL requires operator-provided mode, episode identifiers, baseline and threshold.

**Verification status:** The original E0 mathematical core suite passed 9/9 local tests; the edge-control and VM-CORE service suites contain 8 and 9 tests, respectively. The H1–H4 regression suite passed 72 tests; the four B01 episodes recorded their expected diagnostic results. GitHub Actions uses the manual `workflow_dispatch` trigger.


## 4. Implementation and repository decisions

1. All repository source, comments, tests, documentation, and commit messages are written in **English** for potential publication and transfer.
2. The deployed architecture contains **five Ubuntu Server 26.04 LTS virtual machines** under Proxmox VE 9.2.2 and **seven application services**. Each VM has its own Docker Compose project under /opt/eacld/{control,nodes,reference,edge,core}.
3. VM networks: Proxmox `vmbr610` NET-DATA (10.60.10.0/24), `vmbr620` NET-PROBE (10.60.20.0/24), `vmbr630` NET-CONTROL (10.60.30.0/24), `vmbr640` NET-PLANT (10.60.40.0/24), and `vmbr1` VLAN 200 for administration (10.100.200.0/24).
4. VM-CONTROL owns the process simulation, private orchestration, injection, and private state. Its NET-PLANT HTTP interface exposes public process observations only.
5. VM-NODES and VM-REFERENCE observe the **same** simulated process through separate acquisition services and communication paths.
6. Telemetry runs through VM-NODES → VM-EDGE G1 → VM-EDGE G2 → VM-CORE. Active checks travel directly from VM-CORE to VM-NODES or VM-REFERENCE over NET-PROBE, bypassing the telemetry gateway.
7. VM-CORE integrates the E0 Bayesian inference and decision engine through `LiveEnvironment`.
8. The V1 technical specification is maintained in Romanian on TUIAȘI Google Drive for the infrastructure implementer; this repository is in English.
9. Runtime secrets, per-node HMAC keys, persistent databases and intervention ground truth remain in access-restricted runtime storage. `.gitignore` and `.dockerignore` exclude secrets and runtime files from source-control and image-build contexts.
10. The original E0 source, configurations and test scripts are maintained in the separate public repository `Mihailescu-Ghiuzan-Chiper-Research/EACLD-Mathematical-Model`. The deployment-oriented E0 integration remains in `core/vendor/e0/`.
11. Both repositories are public under the GitHub organization `Mihailescu-Ghiuzan-Chiper-Research`.

## 5. Reference documents and locations

**Technical architecture (implementation authority):**  
TUIAȘI Google Drive → PhD TUIASI → 2 Direcții de cercetare → 04 EACLD – diagnostic cauzal → 02 Testbed experimental → "EACLD - Arhitectura si implementarea testbedului experimental - V1.docx". Research architecture folder: https://drive.google.com/drive/folders/111T-Dr2pTu4cmwwpYxrpn9ZKcazLb7sI?usp=sharing.

**Publication supplement:**  
TUIAȘI Google Drive → PhD TUIASI → 3 Activitatea de publicare → 04 Activitate publicare 2026-2027 (Anul V) → 004 MDPI Information = ÎN LUCRU → 01 Manuscris → `EACLD_S2_MDPI_Information_V3.docx` and `EACLD_S3_MDPI_Information_V3.docx` (active versions; V1 and V2 retained).

**Research continuity and collaboration protocol:**  
Consult the TUIAȘI research project documentation and the Google Drive document "README - MDPI Information - Orientare și continuitate". Follow the approved architecture and document formatting. Record implementation, proposals and verification results distinctly.

**Distributed H1–H4 execution protocol:**  
TUIAȘI Google Drive → same shared testbed folder as architecture V1 → "EACLD – Protocolul de execuție a experimentelor și validare a rezultatelor" (native Google Doc, edited in place). A verified Word export is stored alongside it as "EACLD - Protocolul de executie a experimentelor H1-H4 - 2026-11-12.docx". Section 3.2 contains executable commands, exact H1–H4 input selection and evidence/artifact checks. The active source branch for those commands is `feature/h4-experiment-runner`.

**Existing E0 computational artifact:**  
"EACLD_E0_Experiment_2026_11_04.zip"; the existing E0 Bayesian core has already been incorporated into VM-CORE under `core/vendor/e0/`. The original computational source is maintained in the separate `EACLD-Mathematical-Model` repository.

## 6. Work log

| Date | Checkpoint | Git reference |
| --- | --- | --- |
| 2026-11-10 | Private GitHub repository established; initial five-VM/seven-service directory layout created | a7a3b714 |
| 2026-11-10 | Shared binary frame, HMAC, MQTT and interface contracts committed with unit tests | b872cbfd |
| 2026-11-10 | Initial eacld-control implementation: virtual plant, private orchestrator/injector/store, read-only NET-PLANT API, Docker configuration and tests | 6c45ef95 |
| 2026-11-10 | Initial eacld-nodes implementation: shared-process sensor acquisition, signed MQTT telemetry, direct challenge, keyring, Compose and 21 local tests; runtime smoke check | c84fdb02 |
| 2026-11-10 | Initial eacld-reference implementation: independent NET-PLANT read, NET-PROBE reference API, NET-CONTROL health API, Compose packaging and 19 local tests; two-listener smoke test | 92452898 |
| 2026-11-10 | VM-EDGE Mosquitto 2.x configuration and initial eacld-g1 byte-preserving MQTT forwarding, internal health and 19 local tests; live-broker integration pending | 18e8101f |
| 2026-11-10 | Initial eacld-g2 MQTT forwarding, one-shot header mutation/replay primitives, dedicated Compose service and 19 local tests; live-broker and control integration pending | 72566a55 |
| 2026-11-10 | VM-EDGE edge-control agent, G2 Unix control channel, 8 tests, Compose and documentation committed; VM integration pending | Current main work sequence |
| 2026-11-10 | VM-CORE telemetry, replay registry, PostgreSQL, preserved Bayesian E0 vendor artifact, LiveEnvironment, 9 new tests and service Compose committed | This commit on main |
| 2026-11-11 | Imported original E0 computational source, configurations, tests and documentation under EACLD-E0/ | 6122138c |
| 2026-11-11 | Moved original E0 source to the separate EACLD-Mathematical-Model repository; retained VM-CORE integration | EACLD-Mathematical-Model b8ac4327 |
| 2026-11-11 | Removed E0 source duplication from EACLD-Testbed; updated repository references | b2af078c |
| 2026-11-11 | Disabled automatic GitHub Actions push triggers; retained manual execution only | 19dd01f7 |
| 2026-11-11 | Added H1 experiment runner, baseline and intervention capture, telemetry-ID guard, persistent diagnosis observation and local tests | feature/h1-experiment-runner |
| 2026-11-11 | Added H2 runtime node-local bias API, one-command experiment runner, evidence capture, automatic restoration and tests | feature/h2-experiment-runner |
| 2026-11-11 | Added H3 G2 original/mutated frame evidence, restricted agent status, VM-CORE exact-frame diagnosis, experiment runner, cleanup and tests | feature/h3-experiment-runner |
| 2026-11-11 | Implemented H4 exact prior-frame replay, G2 wire evidence, operator runner, VM-CORE stale-frame selection and focused tests; updated experiment and service READMEs | feature/h4-experiment-runner |
| 2026-11-11 | Added H1–H4 common CLI compatibility tests and consolidated local regression command; locally reran historical H1 and H2 operator test snapshots (3/3 and 4/4) | feature/h4-experiment-runner |
| 2026-11-12 | Restored original E0 `eacld/simulator.py` to the vendored archive in both branches, correcting the source-package import defect without changing the Bayesian engine | main `333bb956`; feature/h4-experiment-runner `841c96b` |
| 2026-11-12 | Corrected consolidated H1–H4 regression runner to extract the E0 archive and set the VM-CORE Python package path | feature/h4-experiment-runner `4629c76` |
| 2026-11-16 | Block B01: H1–H4 executed across five Proxmox VMs; four recorded episode manifests and 72 passing regression tests | feature/h4-experiment-runner `68a75fff317318296f3ada7b7e20d193f5bd04db` |

## 7. H1–H4 experiment interfaces

**H1 — process intervention.** The `feature/h1-experiment-runner` branch adds `control/experiments/h1_run.py`, restricted VM-CORE evidence retrieval and an optional `expected_telemetry_id` guard for diagnosis of the latest authenticated telemetry. The operator procedure initializes the common process, schedules a process-level H1 intervention, records the resulting observations and saves the diagnostic decision alongside private intervention evidence held on VM-CONTROL. Tests and instructions are in `control/tests/`, `core/tests/` and `control/experiments/README.md`.

**H2 — sensor measurement bias.** The `feature/h2-experiment-runner` branch implements the H2 measurement-bias interface. VM-NODES accepts VM-CONTROL-restricted, in-memory bias changes per selected node. `control/experiments/h2_run.py` applies the bias, checks the unchanged common process, diagnoses the selected authenticated measurement, records the evidence and restores the original bias. Tests are in `nodes/tests/test_bias_control.py` and `control/tests/test_h2_run.py`.

**H3 — gateway telemetry mutation.** The `feature/h3-experiment-runner` branch implements the H3 gateway mutation and telemetry-selection interfaces. G2 records the original and XOR-modified 94-byte frames for a one-shot header mutation while preserving the original HMAC. VM-CORE supports exact payload lookup and diagnosis of a selected persisted telemetry ID, including after newer MQTT messages arrive. `control/experiments/h3_run.py` collects G2 and VM-CORE evidence and clears the intervention. Focused tests are in `edge/tests/test_h3_mutation_evidence.py`, `core/tests/test_h3_core_selection.py` and `control/tests/test_h3_run.py`.

**H4 — authentic telemetry replay.** The `feature/h4-experiment-runner` branch implements the H4 authenticated-frame replay and stale-telemetry selection. G2 maintains a bounded forwarding history and stages one previously forwarded 94-byte frame selected by exact bytes. When newer telemetry arrives for the same node and boot, G2 forwards it and retransmits the older frame unchanged. The event records the reference, triggering frame and replayed frame. `control/experiments/h4_run.py` correlates the original authenticated, fresh record with the newer trigger and the duplicated authenticated, stale record in VM-CORE. B6 inference uses the exact stale record; the E0 engine and existing diagnostic routes are reused. The G2 intervention is cleared on completion or error. Tests are in `edge/tests/test_h4_replay_evidence.py`, `core/tests/test_h4_replay_selection.py` and `control/tests/test_h4_run.py`. A cross-runner compatibility suite was added at `control/tests/test_experiment_compatibility.py`; `control/experiments/verify_h1_h4.sh` executes the focused unit/API suites in sequence. The consolidated regression suite passed 72 tests on the five-VM environment during block B01.

The H1–H4 experiment code and associated READMEs reside in the feature-branch history, culminating in `feature/h4-experiment-runner`. The central status file is maintained on `main` and synchronized into the active development branch.

## 8. How to resume

1. Open README.md and this central PROJECT_STATUS.md from main.
2. Read the current architecture V1 from the TUIAȘI research directory before modifying implementation contracts.
3. Inspect main for the initial services and `feature/h4-experiment-runner` for the cumulative H1–H4 experimental implementation.
4. Execute further H1–H4 blocks using the deployed Proxmox testbed and evaluate the recorded evidence.
5. Update this central PROJECT_STATUS.md on main after each implementation checkpoint, recording the feature branch, code locations and test results. The corrected E0 source archive and manual GitHub Actions workflow are documented in Section 2.

