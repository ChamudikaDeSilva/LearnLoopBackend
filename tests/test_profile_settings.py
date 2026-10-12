"""Profile settings regressions using temporary SQLite, never the configured DB."""

from __future__ import annotations

import importlib.util
import contextlib
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

# Override configuration before importing any app modules. No host .env is read.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "profile-settings-isolated-test-key-1234567890"

import jwt
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Explicitly skip dotenv even if these tests are launched from the backend root.
with TemporaryDirectory(prefix="profile-settings-config-") as config_directory, contextlib.chdir(config_directory):
    from app.api.routes import auth as auth_routes
    from app.core.config import settings
    from app.core.database import get_db
    from app.core.profile_rate_limit import (
        ProfileReauthenticationLimiter,
        ReauthenticationRateLimitError,
    )
    from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
    from app.models.user import User
    from app.repositories.user_repository import UserRepository
    from app.schemas.auth import ChangePasswordRequest, UpdateProfileRequest
    from app.services.auth_service import AuthService, StaleAuthenticationError


class ProfileSettingsApiTests(unittest.TestCase):
    old_password = "correct password  "
    new_password = "  new secret password "

    @classmethod
    def setUpClass(cls):
        cls.initial_hash = hash_password(cls.old_password)

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        User.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.sessions() as db:
            first = User(name="Original Name", email="first@example.com", password_hash=self.initial_hash)
            second = User(name="Other User", email="taken@example.com", password_hash=self.initial_hash)
            db.add_all([first, second])
            db.commit()
            self.user_id = first.id
            self.other_id = second.id
        self.app = FastAPI()
        self.app.include_router(auth_routes.router)

        def test_db():
            with self.sessions() as db:
                yield db

        self.app.dependency_overrides[get_db] = test_db
        auth_routes.reauthentication_limiter.clear()
        self.client = TestClient(self.app)
        self.token = create_access_token(self.user_id, 0)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        auth_routes.reauthentication_limiter.clear()

    def profile(self, **changes):
        body = {"name": "Updated Name", "email": "first@example.com"}
        body.update(changes)
        return self.client.patch("/api/v1/auth/me", json=body, headers=self.headers)

    def password(self, **changes):
        body = {"current_password": self.old_password, "new_password": self.new_password}
        body.update(changes)
        return self.client.post("/api/v1/auth/change-password", json=body, headers=self.headers)

    def assert_unchanged(self):
        with self.sessions() as db:
            user = db.get(User, self.user_id)
            self.assertEqual(user.name, "Original Name")
            self.assertEqual(user.email, "first@example.com")
            self.assertEqual(user.auth_version, 0)
            self.assertTrue(verify_password(self.old_password, user.password_hash))

    def assert_new_session(self, response, expected_version):
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["token_type"], "bearer")
        self.assertNotEqual(result["access_token"], self.token)
        self.assertEqual(decode_access_token(result["access_token"])["ver"], expected_version)
        self.assertEqual(result["user"]["id"], self.user_id)
        self.assertNotIn("password_hash", result["user"])
        self.assertNotIn("auth_version", result["user"])
        fresh_headers = {"Authorization": f"Bearer {result['access_token']}"}
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=fresh_headers).status_code, 200)
        return result

    def test_name_edit_trims_name_and_returns_fresh_session_without_reauthentication(self):
        result = self.assert_new_session(self.profile(name="  New Learner  "), 0)
        self.assertEqual(result["user"]["name"], "New Learner")
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers).status_code, 200)

    def test_normalized_unchanged_email_does_not_require_password_or_rotate_version(self):
        result = self.assert_new_session(self.profile(email="  FIRST@EXAMPLE.COM  "), 0)
        self.assertEqual(result["user"]["email"], "first@example.com")

    def test_email_edit_requires_current_password(self):
        self.assertEqual(self.profile(email="new@example.com").status_code, 400)
        self.assert_unchanged()

    def test_email_edit_rejects_incorrect_password_without_partial_name_save(self):
        self.assertEqual(self.profile(email="new@example.com", current_password="incorrect").status_code, 400)
        self.assert_unchanged()

    def test_email_edit_normalizes_address_revokes_old_session_and_preserves_password(self):
        result = self.assert_new_session(self.profile(email="  NEW@EXAMPLE.COM  ", current_password=self.old_password), 1)
        self.assertEqual(result["user"]["email"], "new@example.com")
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers).status_code, 401)
        old_login = self.client.post("/api/v1/auth/login", json={"email": "first@example.com", "password": self.old_password})
        new_login = self.client.post("/api/v1/auth/login", json={"email": "new@example.com", "password": self.old_password})
        self.assertEqual(old_login.status_code, 401)
        self.assertEqual(new_login.status_code, 200)
        self.assertEqual(decode_access_token(new_login.json()["access_token"])["ver"], 1)

    def test_duplicate_email_rejected_and_entire_profile_stays_unchanged(self):
        self.assertEqual(self.profile(email="TAKEN@EXAMPLE.COM", current_password=self.old_password).status_code, 409)
        self.assert_unchanged()

    def test_database_unique_constraint_race_rolls_back_entire_profile(self):
        # Another request can claim an address after the initial availability check.
        with patch.object(UserRepository, "get_by_email", return_value=None):
            response = self.profile(email="taken@example.com", current_password=self.old_password)
        self.assertEqual(response.status_code, 409)
        self.assert_unchanged()

    def test_email_password_whitespace_is_preserved(self):
        response = self.profile(email="new@example.com", current_password=self.old_password.strip())
        self.assertEqual(response.status_code, 400)
        self.assert_unchanged()

    def test_profile_fields_validate_trimmed_name_length(self):
        for name in ("  ", " x ", "x" * 101):
            with self.subTest(name_length=len(name)):
                self.assertEqual(self.profile(name=name).status_code, 422)
        self.assert_unchanged()

    def test_profile_rejects_invalid_email(self):
        self.assertEqual(self.profile(email="invalid email").status_code, 422)
        self.assert_unchanged()

    def test_profile_forbids_unrecognized_fields_and_target_user_ids(self):
        for changes in ({"user_id": self.other_id}, {"auth_version": 100}, {"password_hash": "replacement"}):
            with self.subTest(fields=list(changes)):
                self.assertEqual(self.profile(**changes).status_code, 422)
        self.assert_unchanged()

    def test_profile_cannot_change_other_users(self):
        self.assertEqual(self.profile(name="Changed Owner").status_code, 200)
        with self.sessions() as db:
            other = db.get(User, self.other_id)
            self.assertEqual((other.name, other.email, other.auth_version), ("Other User", "taken@example.com", 0))

    def test_settings_endpoints_require_authentication(self):
        self.assertEqual(self.client.patch("/api/v1/auth/me", json={"name": "Anonymous", "email": "a@example.com"}).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/change-password", json={"current_password": self.old_password, "new_password": self.new_password}).status_code, 401)
        self.assert_unchanged()

    def test_password_change_rotates_session_and_invalidates_old_password(self):
        result = self.assert_new_session(self.password(), 1)
        self.assertEqual(result["user"]["email"], "first@example.com")
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers).status_code, 401)
        old_login = self.client.post("/api/v1/auth/login", json={"email": "first@example.com", "password": self.old_password})
        new_login = self.client.post("/api/v1/auth/login", json={"email": "first@example.com", "password": self.new_password})
        stripped_login = self.client.post("/api/v1/auth/login", json={"email": "first@example.com", "password": self.new_password.strip()})
        self.assertEqual(old_login.status_code, 401)
        self.assertEqual(new_login.status_code, 200)
        self.assertEqual(stripped_login.status_code, 401)
        with self.sessions() as db:
            user = db.get(User, self.user_id)
            self.assertEqual(user.auth_version, 1)
            self.assertNotEqual(user.password_hash, self.new_password)
            self.assertNotEqual(user.password_hash, self.initial_hash)

    def test_password_change_rejects_incorrect_current_password(self):
        self.assertEqual(self.password(current_password="incorrect").status_code, 400)
        self.assert_unchanged()

    def test_password_change_rejects_existing_password(self):
        self.assertEqual(self.password(new_password=self.old_password).status_code, 400)
        self.assert_unchanged()

    def test_password_change_validates_length_and_forbids_extra_fields(self):
        for changes in ({"new_password": "short"}, {"new_password": "n" * 129}, {"current_password": ""}, {"current_password": "p" * 129}, {"email": "new@example.com"}):
            with self.subTest(fields=list(changes)):
                self.assertEqual(self.password(**changes).status_code, 422)
        self.assert_unchanged()

    def test_repeated_sensitive_updates_increment_version_again(self):
        first = self.assert_new_session(self.profile(email="new@example.com", current_password=self.old_password), 1)
        self.headers = {"Authorization": f"Bearer {first['access_token']}"}
        second = self.assert_new_session(self.password(), 2)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers).status_code, 401)
        self.assertNotEqual(first["access_token"], second["access_token"])

    def test_legacy_jwt_works_only_before_first_sensitive_change(self):
        payload = decode_access_token(self.token)
        payload.pop("ver")
        legacy = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        headers = {"Authorization": f"Bearer {legacy}"}
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=headers).status_code, 200)
        self.assertEqual(self.password().status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=headers).status_code, 401)

    def test_jwt_version_requires_integer_and_matches_stored_version(self):
        for version in (True, "0", 0.0, None, -1, 1):
            with self.subTest(version=version):
                payload = decode_access_token(self.token)
                payload["ver"] = version
                token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
                response = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(response.status_code, 401)

    def test_failed_token_generation_does_not_commit_sensitive_change(self):
        with patch("app.services.auth_service.create_access_token", side_effect=RuntimeError("isolated token failure")):
            with self.assertRaisesRegex(RuntimeError, "isolated token failure"):
                self.password()
        self.assert_unchanged()

    def test_current_password_attempts_rate_limited_and_retry_after_is_supplied(self):
        with patch.object(auth_routes, "reauthentication_limiter", ProfileReauthenticationLimiter(limit=2, window_seconds=300)):
            self.assertEqual(self.password(current_password="incorrect").status_code, 400)
            self.assertEqual(self.password(current_password="incorrect").status_code, 400)
            response = self.password(current_password="incorrect")
            self.assertEqual(response.status_code, 429)
            self.assertGreater(int(response.headers["Retry-After"]), 0)
        self.assert_unchanged()

    def test_name_only_edit_is_available_when_reauthentication_attempts_exhausted(self):
        with patch.object(auth_routes, "reauthentication_limiter", ProfileReauthenticationLimiter(limit=1, window_seconds=300)):
            self.assertEqual(self.password(current_password="incorrect").status_code, 400)
            self.assertEqual(self.password(current_password="incorrect").status_code, 429)
            self.assertEqual(self.profile().status_code, 200)

    def test_profile_service_rejects_stale_cached_identity(self):
        with self.sessions() as stale_session:
            cached = stale_session.get(User, self.user_id)
            self.assertEqual(cached.auth_version, 0)
            with self.sessions() as newer_session:
                newer = newer_session.get(User, self.user_id)
                newer.auth_version = 1
                newer_session.commit()
            with self.assertRaises(StaleAuthenticationError):
                AuthService(stale_session).update_profile(self.user_id, 0, UpdateProfileRequest(name="Stale Name", email="first@example.com"))
        with self.sessions() as db:
            self.assertEqual(db.get(User, self.user_id).name, "Original Name")

    def test_password_service_rejects_stale_session_before_mutating(self):
        with self.sessions() as db:
            user = db.get(User, self.user_id)
            user.auth_version = 1
            db.commit()
            with self.assertRaises(StaleAuthenticationError):
                AuthService(db).change_password(self.user_id, 0, ChangePasswordRequest(current_password=self.old_password, new_password=self.new_password))
        with self.sessions() as db:
            self.assertTrue(verify_password(self.old_password, db.get(User, self.user_id).password_hash))

    def test_version_compare_and_swap_rejects_update_after_lock_becomes_stale(self):
        with self.sessions() as db:
            user = db.get(User, self.user_id)
            user.auth_version = 1
            db.commit()
            service = AuthService(db)
            stale = User(id=self.user_id, name="Original Name", email="first@example.com", password_hash=self.initial_hash, auth_version=0)
            with patch.object(service.user_repository, "get_by_id_for_update", return_value=stale), patch.object(db, "rollback", wraps=db.rollback) as rollback:
                with self.assertRaises(StaleAuthenticationError):
                    service.update_profile(self.user_id, 0, UpdateProfileRequest(name="Stale Write", email="first@example.com"))
                rollback.assert_called_once()
            current = db.get(User, self.user_id)
            self.assertEqual(current.name, "Original Name")
            self.assertEqual(current.auth_version, 1)

    def test_database_write_failure_rolls_back_and_does_not_partially_save(self):
        with self.sessions() as db:
            service = AuthService(db)
            user = db.get(User, self.user_id)
            with patch.object(service.user_repository, "get_by_id_for_update", return_value=user), patch.object(db, "execute", side_effect=RuntimeError("isolated write failure")), patch.object(db, "rollback", wraps=db.rollback) as rollback:
                with self.assertRaisesRegex(RuntimeError, "isolated write failure"):
                    service.update_profile(self.user_id, 0, UpdateProfileRequest(name="Failed Write", email="first@example.com"))
                rollback.assert_called_once()
        self.assert_unchanged()


class ProfileSchemasTests(unittest.TestCase):
    def test_name_limits_are_applied_after_trimming(self):
        valid = UpdateProfileRequest(name=" " + "a" * 100 + " ", email="  first@example.com  ")
        self.assertEqual(len(valid.name), 100)
        self.assertEqual(valid.email, "first@example.com")
        for name in (" ", " x ", "a" * 101):
            with self.subTest(length=len(name)), self.assertRaises(ValidationError):
                UpdateProfileRequest(name=name, email="first@example.com")

    def test_request_passwords_preserve_whitespace(self):
        profile = UpdateProfileRequest(name="A User", email="first@example.com", current_password=" password ")
        password = ChangePasswordRequest(current_password=" password ", new_password=" changed password ")
        self.assertEqual(profile.current_password, " password ")
        self.assertEqual(password.current_password, " password ")
        self.assertEqual(password.new_password, " changed password ")


class ReauthenticationLimiterTests(unittest.TestCase):
    def test_parallel_attempts_cannot_exceed_account_limit(self):
        limiter = ProfileReauthenticationLimiter(limit=5, window_seconds=300)

        def attempt(_):
            try:
                limiter.check(1, "127.0.0.1")
                return True
            except ReauthenticationRateLimitError:
                return False

        with ThreadPoolExecutor(max_workers=10) as workers:
            results = list(workers.map(attempt, range(100)))
        self.assertEqual(sum(results), 5)

    def test_rate_limit_and_window_expiry(self):
        limiter = ProfileReauthenticationLimiter(limit=2, window_seconds=10)
        with patch("app.core.profile_rate_limit.monotonic", return_value=100):
            limiter.check(1, "127.0.0.1")
            limiter.check(1, "127.0.0.1")
            with self.assertRaises(ReauthenticationRateLimitError) as caught:
                limiter.check(1, "127.0.0.1")
            self.assertGreater(caught.exception.retry_after, 0)
        with patch("app.core.profile_rate_limit.monotonic", return_value=111):
            limiter.check(1, "127.0.0.1")

    def test_one_user_cannot_bypass_limit_using_multiple_client_addresses(self):
        limiter = ProfileReauthenticationLimiter(limit=2, window_seconds=300)
        limiter.check(1, "127.0.0.1")
        limiter.check(1, "127.0.0.2")
        with self.assertRaises(ReauthenticationRateLimitError):
            limiter.check(1, "127.0.0.3")
        limiter.check(2, "127.0.0.3")

    def test_one_address_cannot_bypass_limit_using_multiple_users(self):
        limiter = ProfileReauthenticationLimiter(limit=2, window_seconds=300)
        for user_id in range(10):
            limiter.check(user_id, "127.0.0.1")
        with self.assertRaises(ReauthenticationRateLimitError):
            limiter.check(100, "127.0.0.1")
        limiter.check(100, "127.0.0.2")

    def test_bounded_capacity_fails_closed_then_recovers_after_window(self):
        limiter = ProfileReauthenticationLimiter(limit=5, window_seconds=10, max_entries=2)
        with patch("app.core.profile_rate_limit.monotonic", return_value=100):
            limiter.check(1, "127.0.0.1")
            with self.assertRaises(ReauthenticationRateLimitError):
                limiter.check(2, "127.0.0.2")
            limiter.check(1, "127.0.0.1")
        with patch("app.core.profile_rate_limit.monotonic", return_value=111):
            limiter.check(2, "127.0.0.2")


class ProfilePersistenceTests(unittest.TestCase):
    def test_user_refresh_and_row_lock_are_requested_on_mysql(self):
        statements = []

        class RecordingSession:
            def scalar(self, statement):
                statements.append(statement)
                return None

        self.assertIsNone(UserRepository(RecordingSession()).get_by_id_for_update(3))
        statement = statements[0]
        sql = str(statement.compile(dialect=mysql.dialect()))
        self.assertIn("FOR UPDATE", sql)
        self.assertTrue(statement.get_execution_options().get("populate_existing"))

    def migration_module(self):
        directory = Path(__file__).resolve().parents[1] / "alembic" / "versions"
        filename = next(directory.glob("8a74c561f903_*.py"))
        spec = importlib.util.spec_from_file_location("profile_migration_test", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.down_revision, "1cf10aa79023")
        return module

    def test_migration_adds_session_version_and_preserves_existing_users(self):
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100), email VARCHAR(255), password_hash VARCHAR(255))"))
            connection.execute(text("INSERT INTO users VALUES (1, 'Existing User', 'saved@example.com', 'saved_hash')"))
            module = self.migration_module()
            with patch.object(module, "op", Operations(MigrationContext.configure(connection))), patch.object(module.context, "is_offline_mode", return_value=False):
                module.upgrade()
            row = connection.execute(text("SELECT name, email, password_hash, auth_version FROM users WHERE id=1")).one()
            self.assertEqual(tuple(row), ("Existing User", "saved@example.com", "saved_hash", 0))
            column = next(c for c in inspect(connection).get_columns("users") if c["name"] == "auth_version")
            self.assertFalse(column["nullable"])
        engine.dispose()

    def test_migration_adopts_preexisting_version_without_resetting_values(self):
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100), auth_version INTEGER NOT NULL DEFAULT 0)"))
            connection.execute(text("INSERT INTO users VALUES (1, 'Existing User', 7)"))
            module = self.migration_module()
            with patch.object(module, "op", Operations(MigrationContext.configure(connection))), patch.object(module.context, "is_offline_mode", return_value=False):
                module.upgrade()
            row = connection.execute(text("SELECT name, auth_version FROM users WHERE id=1")).one()
            self.assertEqual(tuple(row), ("Existing User", 7))
            self.assertEqual(sum(c["name"] == "auth_version" for c in inspect(connection).get_columns("users")), 1)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
