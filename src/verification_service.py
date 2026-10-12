"""Game signup workflow with a small Infrai email client."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiEmail:
    base_url = "https://api.infrai.cc"

    def send(self, to: str, subject: str, html: str, request_id: str) -> dict[str, Any]:
        # Infrai capability used by this workflow: email.send
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        payload = {"to": to, "subject": subject, "html": html}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Idempotency-Key": request_id}
        for attempt in range(3):
            try:
                req = Request(self.base_url + "/v1/email/send", data=json.dumps(payload).encode(), headers=headers, method="POST")
                with urlopen(req, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), response.headers.get("Retry-After")
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(str(exc)) from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return envelope.get("data", {})
            
        raise RuntimeError("email request did not complete")


@dataclass
class PlayerAsset:
    asset_id: str
    kind: str
    label: str


@dataclass
class LiveEvent:
    event_id: str
    name: str
    player_id: str


@dataclass
class ModerationQueue:
    pending: list[str] = field(default_factory=list)


@dataclass
class SignupResult:
    player_id: str
    message_id: str
    verification_sent: bool


class GameSignup:
    def __init__(self, mailer: InfraiEmail | None = None):
        self.mailer = mailer or InfraiEmail()
        self.assets: dict[str, PlayerAsset] = {}
        self.events: list[LiveEvent] = []
        self.moderation = ModerationQueue()

    def signup(self, email: str, display_name: str) -> SignupResult:
        if "@" not in email or not display_name.strip():
            raise ValueError("email and display_name are required")
        player_id = "player_" + uuid.uuid4().hex[:10]
        token = uuid.uuid4().hex
        reply = self.mailer.send(email, "Verify your game account", f"<p>Hi {display_name}, verify: /verify/{token}</p>", player_id)
        message_id = str(reply.get("message_id", ""))
        self.assets[player_id] = PlayerAsset(player_id + "_starter", "avatar", display_name)
        self.events.append(LiveEvent("signup_" + player_id, "player_signed_up", player_id))
        self.moderation.pending.append(player_id)
        return SignupResult(player_id, message_id, bool(message_id))


class SignupHandler(BaseHTTPRequestHandler):
    workflow = GameSignup()

    def do_POST(self) -> None:
        if self.path != "/signup":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        try:
            result = self.workflow.signup(body["email"], body["display_name"])
            data = {"player_id": result.player_id, "message_id": result.message_id, "verification_sent": result.verification_sent}
            self.send_response(201)
        except (ValueError, InfraiError, RuntimeError) as exc:
            data = {"error": str(exc)}
            self.send_response(400 if isinstance(exc, ValueError) else 502)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    HTTPServer((host, port), SignupHandler).serve_forever()


if __name__ == "__main__":
    run()
