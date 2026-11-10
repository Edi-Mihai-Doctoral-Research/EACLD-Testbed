"""EACLD G2: MQTT forwarding with explicitly staged, one-shot interventions.

Normal forwarding preserves every byte. A future edge-control agent may stage
header mutation or replay; G2 does not start experiments autonomously and
never has HMAC keys or re-signs frames.
"""
from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
import threading

from eacld_contracts.topics import G1_TRANSIT_SUBSCRIPTION, accepted_topic

LOGGER = logging.getLogger(__name__)
SERVICE_VERSION = "0.1.0"
HEADER_SIZE = 62
FRAME_SIZE = 94
HEALTH_HOST = "127.0.0.1"
HEALTH_PORT = 8300


@dataclass(frozen=True)
class Mutation:
    offset: int
    xor_mask: int


@dataclass(frozen=True)
class Replay:
    payload: bytes


def route_transit_topic(topic: str) -> tuple[int, str]:
    """Accept only canonical transit/g1/<uint16> topics."""
    if not isinstance(topic, str):
        raise ValueError("MQTT topic must be text")
    parts = topic.split("/")
    if len(parts) != 3 or parts[:2] != ["transit", "g1"]:
        raise ValueError("only transit/g1/<node_id> is accepted")
    segment = parts[2]
    if not segment or not segment.isascii() or not segment.isdecimal():
        raise ValueError("node_id must use ASCII decimal digits")
    node_id = int(segment)
    if node_id > 65535 or str(node_id) != segment:
        raise ValueError("node_id must be canonical unsigned 16-bit decimal")
    return node_id, accepted_topic(node_id)


def _check_node_id(node_id: int) -> None:
    if type(node_id) is not int or not 0 <= node_id <= 65535:
        raise ValueError("node_id must be an unsigned 16-bit integer")


class Gateway2:
    """The future control agent can stage one action per node, once per frame.

    Interventions are deliberately not activated via environment variables,
    unauthenticated HTTP endpoints, or MQTT payloads. A separate controlled
    integration with eacld-edge-control remains to be implemented.
    """

    def __init__(self) -> None:
        self.ready = threading.Event()
        self._subscription_mid: int | None = None
        self._lock = threading.Lock()
        self._pending: dict[int, Mutation | Replay] = {}
        self._last_forwarded: dict[int, bytes] = {}

    def stage_mutation(self, node_id: int, *, offset: int, xor_mask: int) -> None:
        """XOR one header byte of the next 94-byte frame; keep MAC unchanged."""
        _check_node_id(node_id)
        if type(offset) is not int or not 0 <= offset < HEADER_SIZE:
            raise ValueError("offset must select an authenticated header byte")
        if type(xor_mask) is not int or not 1 <= xor_mask <= 255:
            raise ValueError("xor_mask must be an integer from 1 to 255")
        with self._lock:
            self._pending[node_id] = Mutation(offset, xor_mask)

    def stage_replay(self, node_id: int) -> None:
        """Replay the last successfully queued 94-byte frame for this node."""
        _check_node_id(node_id)
        with self._lock:
            previous = self._last_forwarded.get(node_id)
            if previous is None:
                raise ValueError("no previously forwarded frame is available")
            self._pending[node_id] = Replay(previous)

    def clear_intervention(self, node_id: int) -> None:
        _check_node_id(node_id)
        with self._lock:
            self._pending.pop(node_id, None)

    def on_connect(self, client, _userdata, _flags, reason_code, _properties) -> None:
        self.ready.clear()
        self._subscription_mid = None
        if reason_code != 0:
            LOGGER.error("G2 MQTT connection rejected: %s", reason_code)
            return
        result, mid = client.subscribe(G1_TRANSIT_SUBSCRIPTION, qos=1)
        if result != 0:
            LOGGER.error("G2 MQTT subscription request failed: %s", result)
            return
        self._subscription_mid = mid

    def on_subscribe(self, _client, _userdata, mid, reason_codes, _properties) -> None:
        if mid != self._subscription_mid:
            return
        if not reason_codes or any(code.is_failure for code in reason_codes):
            self.ready.clear()
            LOGGER.error("G2 MQTT subscription was rejected")
            return
        self.ready.set()

    def on_disconnect(self, _client, _userdata, _flags, _reason_code, _properties) -> None:
        self.ready.clear()
        self._subscription_mid = None

    def on_message(self, client, _userdata, message) -> None:
        try:
            node_id, target = route_transit_topic(message.topic)
        except ValueError:
            LOGGER.warning("G2 ignored message on an invalid transit topic")
            return
        payload = message.payload
        if not isinstance(payload, bytes):
            LOGGER.warning("G2 ignored an MQTT payload that was not bytes")
            return

        with self._lock:
            action = self._pending.get(node_id)
            outgoing = payload
            if isinstance(action, Mutation) and len(payload) == FRAME_SIZE:
                changed = bytearray(payload)
                changed[action.offset] ^= action.xor_mask
                outgoing = bytes(changed)
            elif isinstance(action, Mutation):
                LOGGER.warning("G2 deferred mutation: frame is not 94 bytes")

            result = client.publish(target, outgoing, qos=1, retain=False)
            if result.rc != 0:
                LOGGER.error("G2 MQTT forwarding failed with code %s", result.rc)
                return
            if len(outgoing) == FRAME_SIZE:
                self._last_forwarded[node_id] = outgoing
            if isinstance(action, Mutation) and len(payload) == FRAME_SIZE:
                self._pending.pop(node_id, None)
            elif isinstance(action, Replay):
                result = client.publish(target, action.payload, qos=1, retain=False)
                if result.rc == 0:
                    self._pending.pop(node_id, None)
                else:
                    LOGGER.error("G2 MQTT replay failed with code %s", result.rc)


def create_health_server(gateway: Gateway2, *, host: str = HEALTH_HOST,
                         port: int = HEALTH_PORT) -> ThreadingHTTPServer:
    """Container-local readiness; no externally published G2 control port."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/healthz":
                self.send_error(404)
                return
            healthy = gateway.ready.is_set()
            body = json.dumps({"status": "ok" if healthy else "unavailable",
                               "service_version": SERVICE_VERSION}).encode("utf-8")
            self.send_response(200 if healthy else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args) -> None:
            pass

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    import paho.mqtt.client as mqtt

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    password_file = Path(os.environ.get("EACLD_G2_MQTT_PASSWORD_FILE", "/run/eacld/mqtt_password"))
    password = password_file.read_text(encoding="utf-8").rstrip("\r\n")
    if not password:
        raise ValueError("G2 MQTT password file is empty")

    gateway = Gateway2()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="eacld-g2",
                         protocol=mqtt.MQTTv311)
    client.username_pw_set("g2", password)
    client.on_connect = gateway.on_connect
    client.on_subscribe = gateway.on_subscribe
    client.on_disconnect = gateway.on_disconnect
    client.on_message = gateway.on_message
    client.reconnect_delay_set(min_delay=1, max_delay=20)

    health_server = create_health_server(gateway)
    thread = threading.Thread(target=health_server.serve_forever,
                              name="g2-health", daemon=True)
    thread.start()
    try:
        host = os.environ.get("EACLD_MQTT_HOST", "mosquitto")
        port = int(os.environ.get("EACLD_MQTT_PORT", "1883"))
        client.connect_async(host, port, keepalive=30)
        client.loop_forever(retry_first_connection=True)
    finally:
        health_server.shutdown()
        health_server.server_close()


if __name__ == "__main__":
    main()
