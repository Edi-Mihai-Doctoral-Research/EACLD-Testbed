# EACLD-Testbed — Project Status and Continuation Log

**Last updated:** 2026-11-10  
**Repository:** eduardmihailescu-creator/EACLD-Testbed  
**Visibility:** Private  
**Working branch:** main  
**Last completed implementation checkpoint:** This commit on main (inspect Git HEAD for its SHA)  
**Current phase:** Development of the distributed testbed services  
**Next task:** Implement eacld-edge-control on VM-EDGE

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
| eacld-edge-control / VM-EDGE | edge/services/edge-control/ | Not implemented | Pending |
| eacld-core / VM-CORE | core/services/core/ | Not implemented | Pending |
| Existing E0 Bayesian engine | core/vendor/e0/ | Integration pending | Preserve existing eacld/core.py; integrate through LiveEnvironment |
| Distributed VM deployment | Five virtual machines | Not verified | Ubuntu 24.04 / Python 3.12 / live Mosquitto and inter-VM tests pending |

Local unit and smoke tests are not evidence of successful distributed deployment.

## 2. Exact continuation point

**Next component: eacld-edge-control on VM-EDGE.** Follow the existing technical architecture V1. Control and timing remain under VM-CONTROL orchestration. This service has not been implemented.

**Completed G2 implementation:** `edge/services/g2/src/g2.py` uses the distinct `g2` MQTT identity, subscribes only to `transit/g1/+`, and publishes only to `accepted/<node_id>` with QoS 1 and retain disabled. Normal forwarding preserves payload bytes, including invalid frames. One-shot internal `stage_mutation` and `stage_replay` primitives support explicitly staged post-authentication header alteration and replay; no MAC recomputation or node keys are available to G2. Mutation changes one header byte in a 94-byte frame, leaving its 32-byte MAC unchanged. Replay sends a stored prior frame after the next current frame. No public control API or autonomous experiment schedule was added.

**VM-EDGE packaging:** `edge/compose.yaml` now includes eacld-g2 with its own Python 3.12 Dockerfile, pinned Paho dependency, private `edge/secrets/g2_mqtt_password` mount and container-local health endpoint. Mosquitto ACL, broker listener, and G1 behavior are unchanged. Only the broker publishes host port `10.60.10.14:1883`. Provision the G2 password privately.

**Verification:** 19 local G2 unit/configuration tests passed in the implementation environment, covering normal forwarding, controlled mutation, one-shot replay, topic routing, readiness, and restricted exposure. They use a fake MQTT client. No real Mosquitto, Docker deployment, five-VM end-to-end connectivity or external control-agent integration has been verified. The tests do not demonstrate successful distributed deployment.

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

**Publication supplement (related, not the implementation source of truth):**  
TUIAȘI Google Drive → PhD TUIASI → 3 Activitatea de publicare → 04 Activitate publicare 2026-2027 (Anul V) → 004 MDPI Information = ÎN LUCRU → 01 Manuscris → "EACLD - Supplementary Material S2 - MDPI Information - V7.docx".

**Research continuity and collaboration protocol:**  
Consult the TUIAȘI research project documentation and the Google Drive document "README - MDPI Information - Orientare și continuitate". Preserve architecture and scope; distinguish implemented, proposed, and verified work without inventing results. Do not change existing document formatting or technical requirements without an explicit decision.

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
| 2026-11-10 | Initial eacld-g2 MQTT forwarding, one-shot header mutation/replay primitives, dedicated Compose service and 19 local tests; live-broker and control integration pending | Current main checkpoint |

## 6. How to resume

1. Open this repository and read README.md, then this PROJECT_STATUS.md.
2. Read the current architecture V1 from the TUIAȘI research directory before modifying implementation contracts.
3. Inspect main and the latest implemented component; use the exact continuation point in Section 2.
4. When new work is completed, update Sections 1, 2, and 5 in the **same commit** as the implementation whenever possible. Record tested scope and its limitations accurately.

This document is a **live checkpoint**, not an automatically generated claim of implementation completeness.
