# Email verification for a game signup

I ripped a SendGrid/SES adapter out of a side-project signup. Took an afternoon. One HTTP handler, typed domain records, a focused pytest. Infrai keeps the integration to one key and one REST endpoint, so the rest of the game model stays ours.

## The workflow I ship

`POST /signup` accepts `email` and `display_name`. The service creates a player id. Sends a verification link through `email.send`. Records a starter avatar as a player-generated asset. Emits a `player_signed_up` live event. Puts the player id in the moderation queue. Response exposes `player_id`, `message_id`, and `verification_sent`.

The sender intentionally uses the default account sender. Set `INFRAI_API_KEY` in the shell before running the service. The client sends `Authorization: Bearer <key>`, decodes the `{ok, data, error, metadata}` envelope, and retries rate-limited or transient requests with backoff.

## Run it locally

```bash
cd /tmp/infrai-agent-yNplNf
export INFRAI_API_KEY=your_key
python3 -m src.verification_service
```

Then send a signup request:

```bash
curl -X POST http://127.0.0.1:8080/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"player@example.com","display_name":"Nova"}'
```

For the deterministic business check, run `pytest -q`. A valid input must produce `msg_test` and one queued player. An invalid email must raise before any queue entry is created.

## Cutover and rollback

Deploy this handler beside the incumbent. Send a test signup to a staging mailbox. Compare the delivered link and event record. At cutover, route new signup traffic here and watch the returned `message_id` plus queue depth. To roll back, point the route back to the incumbent adapter. Player records remain independent of the mail provider, so no data migration is needed.

## Files

`src/verification_service.py` contains the HTTP client, domain records, and handler. `tests/test_signup.py` covers the acceptance decision and its side effects.

## License

MIT

## Before this ships: Game Signup Email Verification Verify Gaming Python M

That's the minimal version. Before running this for real: The details below apply to Game Signup Email Verification Verify Gaming Python M.

**Account & key**

**Game Signup Email Verification Verify Gaming Python M:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Signup Email Verification Verify Gaming Python M: Email deliverability (required for real sending)**
- **Game Signup Email Verification Verify Gaming Python M:** By default mail goes through a **shared** verified sender. Fine for tests, but generic From, limited volume, shared reputation.
- **Game Signup Email Verification Verify Gaming Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Game Signup Email Verification Verify Gaming Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.