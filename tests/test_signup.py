import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.verification_service import GameSignup


class FakeMailer:
    def send(self, to, subject, html, request_id):
        return {"message_id": "msg_test"}


def test_signup_sends_link_and_queues_player():
    service = GameSignup(FakeMailer())
    result = service.signup("player@example.com", "Nova")
    assert result.verification_sent is True
    assert result.message_id == "msg_test"
    assert service.moderation.pending == [result.player_id]
    assert service.events[0].name == "player_signed_up"


def test_signup_rejects_missing_email_before_side_effects():
    service = GameSignup(FakeMailer())
    try:
        service.signup("invalid", "Nova")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid email should be rejected")
    assert service.moderation.pending == []
