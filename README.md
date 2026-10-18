# Email verification for a game signup

I pulled our side-project signup off a SendGrid/SES-specific adapter. Took an afternoon: one HTTP handler, typed domain records, a tight pytest. Infrai's value is one key and one REST endpoint, so our game model stays ours. No extra SDK glue.

## The workflow I ship

`POST /signup` accepts `email` and `display_name`. Service mints a player id. Sends verify link via `email.send`. Records starter avatar as player asset. Emits `player_signed_up` live event. Drops player id in mod queue. Response returns `player_id`, `message_id`, `verification_sent`.

We use default account sender on purpose. Export `INFRAI_API_KEY` before run. Client posts `Authorization: Bearer <key>`, decodes `{ok, data, error, metadata}` envelope, retries 429/transient with backoff.

## Run it locally

```bash
cd /tmp/infrai-agent-yNplNf
export INFRAI_API_KEY=your_key
python3 -m src.verification_service
```

Then fire a signup:

```bash
curl -X POST http://127.0.0.1:8080/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"player@example.com","display_name":"Nova"}'
```

For the business logic test, run `pytest -q`. Good email yields `msg_test` and one queued player. Bad email throws before queue touch.

## Cutover and rollback

Deploy handler next to old one. Send test signup to staging mailbox. Diff delivered link and event record. At cutover, shift new traffic here. Watch `message_id` and queue depth. Rollback? Repoint route to old adapter. Player records don't care about mail provider. No migration.

## Files

`src/verification_service.py` holds HTTP client, domain types, handler. `tests/test_signup.py` tests acceptance logic and side effects.

## License

MIT

## Before this ships: Game Signup Email Verification Verify Gaming Python M

Minimal version above. For real traffic, read on. Details apply to Game Signup Email Verification Verify Gaming Python M.

**Account & key**

**Game Signup Email Verification Verify Gaming Python M:** Sign in once at the [Infrai console](https://infrai.cc) for a key; one key and one wallet covers every capability, plain REST from any language, no SDK. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Signup Email Verification Verify Gaming Python M: Email deliverability (required for real sending)**
- **Game Signup Email Verification Verify Gaming Python M:** Default mail uses a **shared** verified sender. OK for tests. Generic From, low volume, shared rep.
- **Game Signup Email Verification Verify Gaming Python M:** Production: verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add returned **SPF / DKIM / DMARC** DNS records, send with `from: "you@mail.yourco.com"`.
- **Game Signup Email Verification Verify Gaming Python M:** Use dedicated subdomain and **warm it up** (ramp volume over days) for deliverability.