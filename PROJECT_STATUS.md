# EACLD-Testbed — Project Status and Continuation Log

**Last updated:** 2026-11-12  
**Repository:** Edi-Mihai-Doctoral-Research/EACLD-Testbed  
**Visibility:** Private  
**Central status branch:** main  
**Main implementation checkpoint:** Seven initial application services committed on main; H1–H4 experiment code developed separately  
**Latest experimental branch:** feature/h4-experiment-runner (includes H1–H3 implementation history)  
**Current phase:** H1–H4 operator implementations committed on feature branches; unit-level consolidation and five-VM integration remain to be completed  
**Next software task:** Execute the consolidated H1–H4 regression suite and resolve any identified integration defects  
**Next infrastructure task:** Mihai to identify temporary hardware resources for a 10-day testbed window, prepare five VMs, deploy the services, and begin end-to-end integration

This file is the **single authoritative implementation checkpoint** for continuation across collaborators and ChatGPT sessions. README.md is the repository entry point; this document holds the current status and chronological work log. The source on each referenced Git branch defines that branch's implementation; main retains the initial service implementation. The V1 architecture document is authoritative for technical requirements.

## 1. Current implementation status

| Area | Location | Status | Verification |
| --- | --- | --- | --- |
| Repository layout | control/, nodes/, reference/, edge/, core/ | Created | Directory layout aligned with architecture V1 |
| Original E0 computational source | EACLD-Mathematical-Model (separate private repository) | Imported and verified | 14 original source, configuration, test and documentation files; source tree identical to archived E0 source |
| Shared binary frame and HMAC-SHA256 | shared/eacld_contracts/frame.py | Implemented | 12 local shared-contract tests passed in previous implementation session |
| MQTT topic and access definitions | shared/eacld_contracts/topics.py | Implemented | Included in shared-contract tests |
| HTTP / LiveEnvironment contracts | shared/eacld_contracts/interfaces.py | Defined | Included in shared-contract tests |
| eacld-control / VM-CONTROL | control/services/control/ | Initial implementation committed | 12 local unit tests passed in previous implementation session |
| eacld-nodes / VM-NODES | nodes/services/nodes/ | Initial implementation committed | 21 local unit/API tests passed; MQTT broker mocked |
| eacld-reference / VM-REFERENCE | reference/services/reference/ | Initial implementation committed | 19 local unit/API tests passed on Python 3.13.5; two HTTP listeners and fresh reference read passed a local smoke test with a stubbed plant |
| eacld-g1 / VM-EDGE | edge/services/g1/ | Initial implementation committed | 19 local unit/configuration tests passed on Python 3.13.5; MQTT forwarding tested with a fake client; real broker not yet tested |
| eacld-g2 / VM-EDGE | edge/services/g2/ | Initial implementation committed | 19 local unit/configuration tests passed on Python 3; MQTT tested with a fake client, live broker pending |
| eacld-edge-control / VM-EDGE | edge/services/edge-control/ | Initial implementation committed | 8 unit/API tests committed; local socket + HTTP integration and live-VM operation not independently verified |
| eacld-core / VM-CORE | core/services/core/ | Initial implementation committed | 9 new tests committed; original E0 core 9/9 tests passed locally; live MQTT/Postgres/VM integration unverified |
| Existing E0 Bayesian engine | core/vendor/e0/e0_source.zip.b64 | Original E0 source and calibrated model vendored without private data | Original SHA-256 verified from Drive; original E0 core tests 9/9 passed locally |
| H1 — process intervention | control/experiments/h1_run.py; restricted VM-CORE telemetry/diagnosis API | Committed on feature/h1-experiment-runner; inherited by H2/H3 branches | Operator and API unit tests added; baseline, injected state and selected diagnostic frame recorded |
| H2 — virtual sensor measurement bias | nodes/services/nodes/src/nodes.py; control/experiments/h2_run.py | Committed on feature/h2-experiment-runner; inherited by H3 branch | Four local runner tests recorded as passed; bias API tests and automatic restoration implemented |
| H3 — G2 telemetry mutation | edge/services/g2/src/g2.py; edge/services/edge-control/src/agent.py; control/experiments/h3_run.py; VM-CORE frame selection | Committed on feature/h3-experiment-runner | Tests added for G2 mutation evidence, exact VM-CORE frame selection and operator cleanup |
| H4 — authentic telemetry replay | edge/services/g2/src/g2.py; edge/services/edge-control/src/agent.py; control/experiments/h4_run.py; VM-CORE sequence registry and exact record selection | Committed on feature/h4-experiment-runner | Tests added for bounded frame capture, authentic stale replay, exact selected diagnosis and cleanup |
| H1–H4 compatibility | control/tests/test_experiment_compatibility.py; control/experiments/verify_h1_h4.sh | Committed on feature/h4-experiment-runner | Shared operator CLI contracts checked by new tests; combined component regression script added |
| Distributed VM deployment | Five virtual machines | Pending | Mihai is coordinating hardware availability, VM setup, networking, and base software; a 10-day infrastructure window has been requested |
| GitHub Actions / service unit tests | .github/workflows/eacld-unit-tests.yml | Manual dispatch only | Seven earlier push-triggered workflow runs failed in the core job; edge job passed in the latest run; no deployment or E2E verification established |


## 2. Completion of the two authorized service implementations

**eacld-edge-control / VM-EDGE: initial implementation committed.** The source-restricted HTTP agent listens on 10.60.30.14:8300 (NET-CONTROL) and authorizes only VM-CONTROL at 10.60.30.10 for intervention requests. G2 has a private Unix-domain command socket shared with the agent through a dedicated Docker volume. Explicit mutate, replay and clear commands stage G2 interventions without autonomously selecting experimental scenarios. The G1 application and Mosquitto ACL/host port remain unchanged. Eight local unit/API tests are committed. Live VM-EDGE integration testing is pending. The edge-control API contract is an implementation-level extension to the V1 health endpoint.

**eacld-core / VM-CORE: initial implementation committed.** Core subscribes only to accepted/+ using the core MQTT principal, parses the original 94-byte frame contract, validates HMAC against VM-CORE-only node keys and persists anti-replay state and received telemetry in internal PostgreSQL 16. The private E0 computational source, fitted model and configuration were selectively copied from the verified Drive archive into a compact reproducible source package without any private ground-truth datasets. E0 eacld/core.py is unmodified and loaded by the container at build time. The LiveEnvironment adapter executes four available physical/security probes and returns only observed results and nominal configured costs. The explicit diagnosis endpoint on VM-CORE NET-CONTROL requires operator-provided mode, episode identifiers, baseline and threshold.

**Verification status:** Original E0 mathematical core tests: 9 passed locally. New tests for edge-control and core services: 8 and 9 committed, respectively. Seven GitHub Actions runs triggered by pushes on 10–11 November 2026 failed in the VM-CORE job: `ModuleNotFoundError: No module named 'eacld.simulator'` during E0 test collection; the latest VM-EDGE job passed. The workflow was changed to `workflow_dispatch` (manual execution only) in commit `19dd01f7`; the import error remains unresolved. Integration testing pending: live Mosquitto, PostgreSQL, Ubuntu/Docker, five-VM connectivity and end-to-end execution. Runtime secrets and private experimental labels are excluded from GitHub.


## 3. Implementation and repository decisions

1. All repository source, comments, tests, documentation, and commit messages are written in **English** for potential publication and transfer.
2. The architecture contains **five Ubuntu Server 24.04 LTS virtual machines** under VMware Workstation Pro and **seven application services**. Each VM has its own Docker Compose project under /opt/eacld/{control,nodes,reference,edge,core}.
3. VM networks: VMnet2 NET-DATA (10.60.10.0/24), VMnet3 NET-PROBE (10.60.20.0/24), VMnet4 NET-CONTROL (10.60.30.0/24), VMnet5 NET-PLANT (10.60.40.0/24), with separate VMnet8 NAT/DHCP for administration.
4. VM-CONTROL owns the process simulation, private orchestration, injection, and private state. Its NET-PLANT HTTP interface exposes public process observations only.
5. VM-NODES and VM-REFERENCE independently observe the **same** simulated process. They have separate acquisition services and paths, not independent physical-process sources.
6. Telemetry runs through VM-NODES → VM-EDGE G1 → VM-EDGE G2 → VM-CORE. Active checks travel directly from VM-CORE to VM-NODES or VM-REFERENCE over NET-PROBE, bypassing the telemetry gateway.
7. The existing E0 Bayesian computational core is reused, not rewritten. VM-CORE integrates it through LiveEnvironment.
8. The V1 technical specification is maintained in Romanian on TUIAȘI Google Drive for the infrastructure implementer; this repository is in English.
9. Secrets, passwords, per-node HMAC keys, runtime databases, and private ground-truth artifacts are not committed to GitHub. The root .dockerignore also excludes local secrets and runtime files from Docker build contexts.
10. The original E0 source, configurations and test scripts are maintained in the separate private repository `Edi-Mihai-Doctoral-Research/EACLD-Mathematical-Model`. The deployment-oriented E0 integration remains in `core/vendor/e0/`.
11. Both repositories were transferred to the GitHub organization `Edi-Mihai-Doctoral-Research` on 11 November 2026; repository access through the TUIAȘI ChatGPT GitHub connector has been restored.

**Division of work:** Mihai prepares the five VMs, networking, and base software, and identifies temporary hardware resources for a 10-day testbed window. An invitation with the Owner role was issued for Mihai in `Edi-Mihai-Doctoral-Research`. The infrastructure assignment and technical documentation were communicated to him by email on 11 November 2026. Repository development covers EACLD application services, integrations, configurations, and tests. Deployment on the prepared VMs and end-to-end verification are joint integration activities.

## 4. Reference documents and locations

**Technical architecture (implementation authority):**  
TUIAȘI Google Drive → PhD TUIASI → 2 Direcții de cercetare → 04 EACLD – diagnostic cauzal → 02 Testbed experimental → "EACLD - Arhitectura si implementarea testbedului experimental - V1.docx". The folder has been shared for Mihai's implementation work: https://drive.google.com/drive/folders/111T-Dr2pTu4cmwwpYxrpn9ZKcazLb7sI?usp=sharing.

**Publication supplement:**  
TUIAȘI Google Drive → PhD TUIASI → 3 Activitatea de publicare → 04 Activitate publicare 2026-2027 (Anul V) → 004 MDPI Information = ÎN LUCRU → 01 Manuscris → "EACLD - Supplementary Material S2 - MDPI Information - V7.docx".

**Research continuity and collaboration protocol:**  
Consult the TUIAȘI research project documentation and the Google Drive document "README - MDPI Information - Orientare și continuitate". Follow the approved architecture and document formatting. Record implementation, proposals and verification results distinctly.

**Distributed H1–H4 execution protocol (updated 12 November 2026):**  
TUIAȘI Google Drive → same shared testbed folder as architecture V1 → "EACLD – Protocolul de execuție a experimentelor și validare a rezultatelor" (native Google Doc, edited in place). A verified Word export is stored alongside it as "EACLD - Protocolul de executie a experimentelor H1-H4 - 2026-11-12.docx". Section 3.2 contains executable commands, exact H1–H4 input selection and evidence/artifact checks. The active source branch for those commands is `feature/h4-experiment-runner`.

**Existing E0 computational artifact:**  
"EACLD_E0_Experiment_2026_11_04.zip"; the existing E0 Bayesian core has already been incorporated into VM-CORE under `core/vendor/e0/`. The original computational source is maintained in the separate `EACLD-Mathematical-Model` repository.

## 5. Work log

| Date | Checkpoint | Git reference |
| --- | --- | --- |
| 2026-11-10 | Private GitHub repository established; initial five-VM/seven-service directory layout created | a7a3b714 |
| 2026-11-10 | README converted to English | cfd8f38f |
| 2026-11-10 | Shared binary frame, HMAC, MQTT and interface contracts committed with unit tests | b872cbfd |
| 2026-11-10 | Initial eacld-control implementation: virtual plant, private orchestrator/injector/store, read-only NET-PLANT API, Docker configuration and tests | 6c45ef95 |
| 2026-11-10 | Project continuation log added and linked from README | a624ca6e |
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
| 2026-11-11 | Transferred both repositories to Edi-Mihai-Doctoral-Research and restored GitHub connector access | Organization transfer |
| 2026-11-11 | Sent Mihai the EACLD-Testbed handoff and technical-documentation folder; requested hardware availability for 10 days | Coordination by email |
| 2026-11-11 | Added H1 experiment runner, baseline and intervention capture, telemetry-ID guard, persistent diagnosis observation and local tests | feature/h1-experiment-runner |
| 2026-11-11 | Added H2 runtime node-local bias API, one-command experiment runner, evidence capture, automatic restoration and tests | feature/h2-experiment-runner |
| 2026-11-11 | Added H3 G2 original/mutated frame evidence, restricted agent status, VM-CORE exact-frame diagnosis, experiment runner, cleanup and tests | feature/h3-experiment-runner |
| 2026-11-11 | Synchronized central PROJECT_STATUS.md on main with H1–H3 feature-branch progress; code remains on feature branches | main |
| 2026-11-11 | Implemented H4 exact prior-frame replay, G2 wire evidence, operator runner, VM-CORE stale-frame selection and focused tests; updated experiment and service READMEs | feature/h4-experiment-runner |
| 2026-11-11 | Synchronized central PROJECT_STATUS.md on main with H4 and next integration checkpoint | main |
| 2026-11-11 | Added H1–H4 common CLI compatibility tests and consolidated local regression command; locally reran historical H1 and H2 operator test snapshots (3/3 and 4/4) | feature/h4-experiment-runner |
| 2026-11-12 | Updated the TUIAȘI shared experimental execution and validation protocol for the implemented H1–H4 runners, exact telemetry selection, commands, evidence and cleanup; exported an eight-page Word copy to the same shared testbed folder | TUIAȘI Drive: experimental protocol and EACLD - Protocolul de executie a experimentelor H1-H4 - 2026-11-12.docx |

## 6. Experimental implementation history (H1–H3)

**H1 — process intervention.** The `feature/h1-experiment-runner` branch adds `control/experiments/h1_run.py`, restricted VM-CORE evidence retrieval and an optional `expected_telemetry_id` guard for diagnosis of the latest authenticated telemetry. The operator procedure initializes the common process, schedules a process-level H1 intervention, records the resulting observations and saves the diagnostic decision alongside private intervention evidence held on VM-CONTROL. Tests and instructions are in `control/tests/`, `core/tests/` and `control/experiments/README.md`.

**H2 — sensor measurement bias.** The `feature/h2-experiment-runner` branch derives from H1. VM-NODES accepts VM-CONTROL-restricted, in-memory bias changes per selected node. `control/experiments/h2_run.py` applies the bias, checks the unchanged common process, diagnoses the selected authenticated measurement, records the evidence and restores the original bias. Tests are in `nodes/tests/test_bias_control.py` and `control/tests/test_h2_run.py`.

**H3 — gateway telemetry mutation.** The `feature/h3-experiment-runner` branch derives from H2 and therefore contains H1 and H2 development work. G2 records the original and XOR-modified 94-byte frames for a one-shot header mutation while preserving the original HMAC. VM-CORE supports exact payload lookup and diagnosis of a selected persisted telemetry ID, including after newer MQTT messages arrive. `control/experiments/h3_run.py` collects G2 and VM-CORE evidence and clears the intervention. Focused tests are in `edge/tests/test_h3_mutation_evidence.py`, `core/tests/test_h3_core_selection.py` and `control/tests/test_h3_run.py`.

**H4 — authentic telemetry replay.** The `feature/h4-experiment-runner` branch extends H3. G2 maintains a bounded forwarding history and stages one previously forwarded 94-byte frame selected by exact bytes. When newer telemetry arrives for the same node and boot, G2 forwards it and retransmits the older frame unchanged. The event records the reference, triggering frame and replayed frame. `control/experiments/h4_run.py` correlates the original authenticated, fresh record with the newer trigger and the duplicated authenticated, stale record in VM-CORE. B6 inference uses the exact stale record; the E0 engine and existing diagnostic routes are reused. The G2 intervention is cleared on completion or error. Tests are in `edge/tests/test_h4_replay_evidence.py`, `core/tests/test_h4_replay_selection.py` and `control/tests/test_h4_run.py`. A cross-runner compatibility suite was added at `control/tests/test_experiment_compatibility.py`; `control/experiments/verify_h1_h4.sh` executes the focused unit/API suites in sequence. Historical H1 and H2 local operator snapshots passed 3 and 4 tests, respectively, on 2026-11-11. H3/H4 focused suites are committed for execution in the configured service environments.

The H1–H4 experiment code and associated READMEs reside in the feature-branch history, culminating in `feature/h4-experiment-runner`. The central status file is maintained on `main` and synchronized into the active development branch.

## 7. How to resume

1. Open README.md and this central PROJECT_STATUS.md from main.
2. Read the current architecture V1 from the TUIAȘI research directory before modifying implementation contracts.
3. Inspect main for the initial services and `feature/h4-experiment-runner` for the cumulative H1–H4 experimental implementation.
4. Continue with H1–H4 procedure integration and unit-level regression verification while the five-VM infrastructure is prepared.
5. Update this central PROJECT_STATUS.md on main after each implementation checkpoint, recording the feature branch, code locations and test results. The previous GitHub Actions E0 import issue and manual workflow dispatch are documented in Section 2.

