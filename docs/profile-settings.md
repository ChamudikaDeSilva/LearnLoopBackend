# Authenticated profile settings

These features work while a user is signed in. They do not send email and require
no SMTP configuration.

Apply `alembic upgrade head` before starting the updated backend. The additive
`8a74c561f903` migration adds `users.auth_version` on a fresh database. If that
column remains from a discarded development migration, it adopts the column and
preserves all values. It does not touch subjects, materials, passwords, or any
old unused recovery table. Run this migration online so the schema can be checked.
Downgrading retains this column and its values; the earlier backend ignores it.

## API

Both endpoints require the user's Bearer token and reject unknown request fields.
Their response matches login: `{user, access_token, token_type: "bearer"}`.
The mobile app replaces its stored token with the returned token.

- `PATCH /api/v1/auth/me`: `{name, email, current_password?}`. Name is trimmed
  and must have 2–100 characters. Email is trimmed, validated, and lowercased.
  Changing only the name does not need a password. Changing email requires the
  current password; incorrect/missing passwords return 400, and an already
  registered address returns 409. Email changes take effect immediately and
  are not verified by email. Account ownership always comes from the bearer
  identity, never a user ID in the request.
- `POST /api/v1/auth/change-password`: `{current_password, new_password}`.
  The current password must have 1–128 characters; the new one must have 8–128
  and differ from the current password. Password whitespace is preserved.
  An incorrect current password or identical new password returns 400.

Email/password changes increment a session version. The current app receives
a fresh JWT, while earlier tokens from this or other devices are rejected with
401. Name changes keep the version. Legacy JWTs without a `ver` claim work only
for accounts at version zero. Failed changes leave account credentials unchanged.

Rows are locked and refreshed inside each edit transaction, and updates also
check the authenticated version. A stale request cannot overwrite an account
after another request changes its credentials. Failed transactions are rolled
back. MySQL provides row-level locking; the additional conditional update protects
version-changing writes when tests use SQLite.

## Credential attempt limits

Credential changes allow five checks per account in five minutes and 25 per
client IP in five minutes. Successful checks count too. Name-only saves are not
throttled. Limits use a thread-safe, bounded in-memory store, return 429 with
`Retry-After`, and reset on process restart. With multiple workers or backend
instances, each process has its own limits; use a shared rate limiter such as
Redis before relying on these limits across a production cluster. The backend
uses the direct connection's client address; only configure forwarded-address
trust for a proxy you control.

## Local verification

Install the test client with `python -m pip install -r requirements-dev.txt`.
Then `python -m unittest discover -s tests -p 'test_profile_settings.py'` uses an
isolated SQLite database and test JWT settings. It sends no email, calls no AI
provider, and reads no project `.env` or application database.
