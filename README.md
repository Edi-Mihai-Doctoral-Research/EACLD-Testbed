# EACLD-Testbed

Evidence-Adaptive Cross-Layer Diagnosis (EACLD) — testbed experimental distribuit.

Acest repository conține structura de lucru a implementării, conform documentului **EACLD – Arhitectura și implementarea testbedului experimental – V1** din directorul de cercetare TUIAȘI.

## Distribuția pe mașini virtuale

| Mașină virtuală | Director din repository | Servicii |
| --- | --- | --- |
| VM-CONTROL | `control/` | `eacld-control` |
| VM-NODES | `nodes/` | `eacld-nodes` |
| VM-REFERENCE | `reference/` | `eacld-reference` |
| VM-EDGE | `edge/` | `eacld-g1`, `eacld-g2`, `eacld-edge-control` |
| VM-CORE | `core/` | `eacld-core`; motorul Bayesian E0 reutilizat |

Directorul fiecărei mașini virtuale corespunde proiectului Docker Compose din `/opt/eacld/<director>/`.

## Structura de implementare

- `control/compose.yaml`, `control/services/control/{Dockerfile,requirements.txt,src/}`
- `nodes/compose.yaml`, `nodes/services/nodes/{Dockerfile,requirements.txt,src/}`
- `reference/compose.yaml`, `reference/services/reference/{Dockerfile,requirements.txt,src/}`
- `edge/compose.yaml`, `edge/services/{g1,g2,edge-control}/{Dockerfile,requirements.txt,src/}`, `edge/config/{mosquitto.conf,acl,passwd}`, `edge/volumes/mosquitto/`
- `core/compose.yaml`, `core/services/core/{Dockerfile,requirements.txt,src/}`, `core/vendor/e0/{eacld/core.py,config/e0_config.json,results/fitted_model.json}`, `core/secrets/pg_password`, `core/volumes/postgres/`

Lista indică structura prevăzută în specificație; fișierele aplicațiilor și configurațiile operaționale vor fi adăugate pe măsură ce sunt implementate. Directoarele goale sunt marcate cu `.gitkeep`.

## Domenii de comunicație

- NET-DATA: VMnet2, 10.60.10.0/24
- NET-PROBE: VMnet3, 10.60.20.0/24
- NET-CONTROL: VMnet4, 10.60.30.0/24
- NET-PLANT: VMnet5, 10.60.40.0/24
- ADMIN: VMnet8, NAT/DHCP

## Delimitarea informațiilor

Datele private ale intervențiilor și cauza reală rămân în VM-CONTROL și nu sunt accesibile VM-CORE. Cheile HMAC ale nodurilor sunt deținute numai de VM-NODES și verificatorul din VM-CORE. `VM-EDGE` nu deține aceste chei.

Artefactul computațional E0 este reutilizat în VM-CORE prin `LiveEnvironment`, fără rescrierea `eacld/core.py`.

**Stadiu:** structura inițială; serviciile nu sunt încă implementate.
