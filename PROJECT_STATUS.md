# EACLD-Testbed — Project Status and Continuation Log

**Last updated:** 2026-11-10  
**Repository:** eduardmihailescu-creator/EACLD-Testbed  
**Visibility:** Private  
**Working branch:** main  
**Last completed implementation checkpoint:** Current main HEAD (see Section 5 and Git history)  
**Current phase:** Development of the distributed testbed services  
**Next task:** Implement eacld-reference on VM-REFERENCE

This file is the **single authoritative implementation checkpoint** for continuation across collaborators and ChatGPT sessions. README.md is the repository entry point; this document holds the current status and chronological work log. The executable source on main is authoritative for implemented code; the V1 architecture document is authoritative for technical requirements.

## 1. Current implementation status

| Area | Location | Status | Verified so far |
| --- | --- | --- | --- |
| Repository layout | control/, nodes/, reference/, edge/, core/ | Created | Directory layout checked against architecture V1 |
| Shared binary frame and HMAC-SHA256 | shared/eacld_contracts/frame.py | Implemented | 12 shared-contract unit tests reported passing locally, across the shared package |
| MQTT topics and principal permissions | shared/eacld_contracts/topics.py | Implemented | Included in shared-contract tests |
| HTTP and LiveEnvironment interface definitions | shared/eacld_contracts/interfaces.py | Defined | Included in shared-contract tests |
| eacld-control / VM-CONTROL | control/services/control/ | Initial implementation committed | 12 local unit tests reported passing |
| eacld-nodes / VM-NODES | nodes/services/nodes/ | Initial implementation committed | 21 unit/API tests passed locally on Python 3.13.5; two-listener smoke test passed; MQTT broker mocked, distributed integration pending |
| eacld-reference / VM-REFERENCE | reference/services/reference/ | Not implemented | Pending |
| eacld-g1 / VM-EDGE | edge/services/g1/ | Not implemented | Pending |
| eacld-g2 / VM-EDGE | edge/services/g2/ | Not implemented | Pending |
| eacld-edge-control / VM-EDGE | edge/services/edge-control/ | Not implemented | Pending |
| eacld-core / VM-CORE | core/services/core/ | Not implemented | Pending |
| Existing E0 Bayesian engine | core/vendor/e0/ | Integration pending | Preserve existing eacld/core.py; integrate via LiveEnvironment |
| Distributed deployment | Five virtual machines | Not yet verified | VM setup and end-to-end tests## 2. Exact continuation point

**Next component: eacld-reference (VM-REFERENCE).** Develop this independent acquisition service in English, adhering to the architecture V1 implementation contracts and existing repository conventions.

Required source structure:

- `reference/services/reference/src/reference.py` — independent observation and HTTP service.
- `reference/services/reference/Dockerfile`, `requirements.txt`, `reference/compose.yaml` — container packaging and deployment.
- Tests and English documentation for the reference read path and restricted control-agent health.

Specified interfaces and information boundaries:

- Read the **same** public process maintained by VM-CONTROL at `10.60.40.10:8100/v1/state` via NET-PLANT, independently of VM-NODES.
- Expose `POST /v1/reference/read` on `10.60.20.13:8201` via NET-PROBE for VM-CORE active checks. The V1 response fields are `temperature_mC`, `status`, and `timestamp`; avoid inventing research-specific failure semantics.
- Expose the specified control-agent `GET /healthz` on `10.60.30.13:8300` via NET-CONTROL, limiting its caller to VM-CONTROL at `10.60.30.10`.
- Keep services bound to the research-network interfaces, not VMnet8 ADMIN. VM-REFERENCE has no NET-DATA interface, no MQTT gateway role and no node HMAC keys.
- Do not expose private cause labels, intervention metadata, or experimental ground truth. VM-REFERENCE and VM-NODES must remain separate observation paths of the **same** virtual process.
- Verify unit/API behavior locally before committing and retain distributed/VM tests as pending until the infrastructure is available.

**Completed VM-NODES implementation notes:** The service includes `src/nodes.py`, `sensor.py`, `frame.py`, and `challenge.py`; the shared 94-byte HMAC frame; node-private keyring and MQTT credential files; a read-only NET-PLANT process client; `raw/<node_id>` MQTT publication; direct type-2 challenge responses; and NET-CONTROL health-only access. The example node IDs, default 1000 ms sampling period, bias values and QoS 1 choice are **implementation defaults**, not approved experimental parameters. The experiment protocol will determine actual population, values, scheduling and test outcomes. Dynamic agent configuration beyond V1's health endpoint has not been implemented.

re provisioned.

Keep experiment procedures and statistical evaluation in the separate experimental protocol rather than inventing them in this implementation log.

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

| 2026-11-10 | Initial eacld-nodes implementation: shared-process sensor acquisition, signed MQTT telemetry, direct challenge, keyring, Compose and 21 local tests; runtime smoke check | Current implementation commit (main HEAD) |

## 6. How to resume

1. Open this repository and read README.md, then this PROJECT_STATUS.md.
2. Read the current architecture V1 from the TUIAȘI research directory before modifying implementation contracts.
3. Inspect main and the latest implemented component; use the exact continuation point in Section 2.
4. When new work is completed, update Sections 1, 2, and 5 in the **same commit** as the implementation whenever possible. Record tested scope and its limitations accurately.

This document is a **live checkpoint**, not an automatically generated claim of implementation completeness.
