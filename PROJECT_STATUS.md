# EACLD-Testbed — Project Status and Continuation Log

**Last updated:** 2026-11-10  
**Repository:** eduardmihailescu-creator/EACLD-Testbed  
**Visibility:** Private  
**Working branch:** main  
**Last completed implementation checkpoint:** This commit on main (inspect Git HEAD for its SHA)  
**Current phase:** All seven initial application service implementations committed; distributed deployment pending  
**Next task:** Deploy the services on five VMs and verify end-to-end integration

This file is the **single authoritative implementation checkpoint** for continuation across collaborators and ChatGPT sessions. README.md is the repository entry point; this document holds the current status and chronological work log. The executable source on main is authoritative for implemented code; the V1 architecture document is authoritative for technical requirements.

## 1. Current implementation status

| Area | Location | Status | Verification |
| --- | --- | --- | --- |
| Repository layout | control/, nodes/, reference/, edge/, core/ | Created | Directory layout aligned with architecture V1 |
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
| Distributed VM deployment | Five virtual machines | Not verified | Ubuntu 24.04 / Python 3.12 / live Mosquitto and inter-VM tests pending |


## 2. Completion of the two authorized service implementations

**eacld-edge-control / VM-EDGE: initial implementation committed.** The source-restricted HTTP agent listens on 10.60.30.14:8300 (NET-CONTROL) and authorizes only VM-CONTROL at 10.60.30.10 for intervention requests. G2 has a private Unix-domain command socket shared with the agent through a dedicated Docker volume. Explicit mutate, replay and clear commands stage G2 interventions without autonomously selecting experimental scenarios. The G1 application and Mosquitto ACL/host port remain unchanged. Eight local unit/API tests are committed. Live VM-EDGE integration testing is pending. The edge-control API contract is an implementation-level extension to the V1 health endpoint.

**eacld-core / VM-CORE: initial implementation committed.** Core subscribes only to accepted/+ using the core MQTT principal, parses the original 94-byte frame contract, validates HMAC against VM-CORE-only node keys and persists anti-replay state and received telemetry in internal PostgreSQL 16. The private E0 computational source, fitted model and configuration were selectively copied from the verified Drive archive into a compact reproducible source package without any private ground-truth datasets. E0 eacld/core.py is unmodified and loaded by the container at build time. The LiveEnvironment adapter executes four available physical/security probes and returns only observed results and nominal configured costs. The explicit diagnosis endpoint on VM-CORE NET-CONTROL requires operator-provided mode, episode identifiers, baseline and threshold.

**Verification status:** Original E0 mathematical core tests: 9 passed locally. New tests for edge-control and core services: 8 and 9 committed, respectively, alongside a GitHub test workflow. GitHub Actions success: not confirmed. Integration testing pending: live Mosquitto, PostgreSQL, Ubuntu/Docker, five-VM connectivity and end-to-end execution. Runtime secrets and private experimental labels are excluded from GitHub.


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

**Division of work:** Mihai prepares the five VMs, networking, and base software. Repository development covers EACLD application services, integrations, configurations, and automated tests. Deployment on the prepared VMs and end-to-end verification are joint integration activities.

## 4. Reference documents and locations

**Technical architecture (implementation authority):**  
TUIAȘI Google Drive → PhD TUIASI → 2 Direcții de cercetare → 04 EACLD – diagnostic cauzal → 02 Testbed experimental → "EACLD - Arhitectura si implementarea testbedului experimental - V1.docx".

**Publication supplement:**  
TUIAȘI Google Drive → PhD TUIASI → 3 Activitatea de publicare → 04 Activitate publicare 2026-2027 (Anul V) → 004 MDPI Information = ÎN LUCRU → 01 Manuscris → "EACLD - Supplementary Material S2 - MDPI Information - V7.docx".

**Research continuity and collaboration protocol:**  
Consult the TUIAȘI research project documentation and the Google Drive document "README - MDPI Information - Orientare și continuitate". Follow the approved architecture and document formatting. Record implementation, proposals and verification results distinctly.

**Existing E0 computational artifact:**  
"EACLD_E0_Experiment_2026_11_04.zip"; its existing eacld/core.py is to be incorporated into VM-CORE under core/vendor/e0 when the integration phase begins.

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

## 6. How to resume

1. Open this repository and read README.md, then this PROJECT_STATUS.md.
2. Read the current architecture V1 from the TUIAȘI research directory before modifying implementation contracts.
3. Inspect main and the latest implemented component; use the exact continuation point in Section 2.
4. When new work is completed, update Sections 1, 2, and 5 in the **same commit** as the implementation whenever possible. Record implemented components and test results.

