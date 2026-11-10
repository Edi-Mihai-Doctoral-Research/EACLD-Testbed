# VM-EDGE: Mosquitto and eacld-g1

This directory contains the VM-EDGE MQTT broker and the first gateway stage defined in the EACLD technical architecture (V1). G2 and the edge control agent are **not implemented yet**.

## Transport and access boundaries

The Mosquitto 2.x broker listens at **10.60.10.14:1883** on NET-DATA (VMnet2). The host-port mapping is limited to that address; no EACLD application port is published on the ADMIN interface (VMnet8). G1 connects to the broker through the local Docker network using `mosquitto:1883`, without a host-published listener.

The four distinct broker identities and topic ACLs are defined in `config/acl`:

| Principal | Subscribe | Publish |
| --- | --- | --- |
| node | None | `raw/+` |
| g1 | `raw/+` | `transit/g1/+` |
| g2 | `transit/g1/+` | `accepted/+` |
| core | `accepted/+` | None |

The four identities are provisioned in the **private, hashed** `config/passwd` database, which is excluded from Git. Each must use a distinct password. Do not disable broker authentication or expand the topic permissions.

G1 consumes a message from `raw/<node_id>` and republishes the payload, byte for byte, to `transit/g1/<node_id>`. It neither checks nor recalculates HMAC, changes frame contents, stores node keys, or suppresses duplicate messages. VM-CORE is responsible for authenticity and freshness verification. G2, once implemented, will be responsible for controlled post-authentication corruption and replay.

The gateway uses MQTT QoS 1 for its incoming subscription and outgoing publish. QoS 1 can deliver duplicates; G1 does not remove them, so the downstream verifier can observe replay/freshness conditions. All G1 output messages use `retain=False`. A successful publish request is not proof that downstream G2 or VM-CORE received a frame.

## Source and deployment

- `services/g1/src/g1.py`: topic mapping, Paho MQTT callback handling and container-local health endpoint.
- `services/g1/Dockerfile`, `services/g1/requirements.txt`: Python 3.12 container image.
- `config/mosquitto.conf`, `config/acl`: V1 broker configuration.
- `compose.yaml`: Mosquitto and G1 containers; G2 and edge-control will be added later.
- `volumes/mosquitto`: runtime persistence on VM-EDGE only.

On VM-EDGE, check out the full repository under `/opt/eacld` and use `/opt/eacld/edge` as the working directory:

    cd /opt/eacld/edge

Before `docker compose up`, **provision the private authentication files**. Create `config/passwd` using the `mosquitto_passwd` utility from Mosquitto 2.x. The password entries must be generated for **node**, **g1**, **g2**, and **core**, using four distinct passwords. For example, when the Mosquitto package is installed on VM-EDGE:

    mosquitto_passwd -c config/passwd node
    mosquitto_passwd config/passwd g1
    mosquitto_passwd config/passwd g2
    mosquitto_passwd config/passwd core

Do not use `-c` after the initial command: it recreates the password database and would remove prior identities. Give the broker container's user read access to `config/passwd`, without making the file world-readable. Provision `secrets/g1_mqtt_password` containing only the plaintext **g1** password and a final newline; this file is mounted read-only into the G1 container, not into VM-NODES or VM-CORE. The separate `node` password is provisioned on VM-NODES using its own secret file. Do not commit either password file.

Ensure that `/opt/eacld/edge/volumes/mosquitto` is writable by the Mosquitto container's user, then start the two available components:

    docker compose up --build -d

The G1 container exposes `GET /healthz` on **127.0.0.1:8300 inside the container only**. It reports `ok` after the broker acknowledges the `raw/+` subscription and `unavailable` otherwise. This endpoint is not published to any VM interface; it is intended for the Docker health check. V1's NET-CONTROL agent at VM-EDGE (10.60.30.14:8300) will be provided later by `eacld-edge-control`.

## Local verification

From the repository root, with Python 3.12:

    PYTHONPATH=edge/services/g1:shared python3 -m unittest discover -s edge/tests -v

The tests check exact topic mapping, byte preservation (including tampered MACs), subscription and reconnect state, container-local HTTP health, broker settings, topic ACLs, and the Compose exposure boundary. Local callback tests use a fake MQTT client; they do **not** establish that a live Mosquitto broker or the distributed VM deployment works. Those checks remain for the integration stage.
