"""Local per-Windows-user accounts for PDF Tools."""

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager


PASSWORD_ITERATIONS = 310_000
MIN_PASSWORD_LENGTH = 12
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
INVITATION_LIFETIME_SECONDS = 7 * 24 * 60 * 60
DUMMY_SALT = b"MITS PDF Utility dummy salt"


class AuthenticationError(ValueError):
    """The account operation could not be completed safely."""


def default_database_path():
    """Return a private database path inside the current Windows user's profile."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    directory = os.path.join(base, "MITS PDF Utility")
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "accounts.sqlite3")


class AuthStore:
    def __init__(self, database_path=None):
        self.database_path = database_path or default_database_path()
        parent = os.path.dirname(os.path.abspath(self.database_path))
        os.makedirs(parent, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA busy_timeout = 10000")
            yield connection
        finally:
            connection.close()

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY COLLATE NOCASE,
                    salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
                    session_version INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS login_attempts (
                    username TEXT PRIMARY KEY COLLATE NOCASE,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    locked_until REAL NOT NULL DEFAULT 0
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS invitations (
                    token_hash BLOB PRIMARY KEY,
                    created_by TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    used_at REAL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "session_version" not in columns:
                connection.execute(
                    "ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 0"
                )
            connection.commit()

    @staticmethod
    def _normalize_username(username):
        value = str(username or "").strip().casefold()
        if not value or len(value) > 64 or any(ord(char) < 32 for char in value):
            raise AuthenticationError("Enter a username of 1 to 64 printable characters.")
        return value

    @staticmethod
    def _validate_password(password):
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise AuthenticationError(
                f"Use a password with at least {MIN_PASSWORD_LENGTH} characters."
            )
        if len(password) > 1024:
            raise AuthenticationError("The password is too long.")
        if not password.strip():
            raise AuthenticationError("The password cannot contain only spaces.")

    @staticmethod
    def _password_hash(password, salt):
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
        )

    def needs_setup(self):
        with self._connect() as connection:
            return connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None

    def create_initial_admin(self, username, password):
        username = self._normalize_username(username)
        self._validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                raise AuthenticationError("Initial administrator setup has already been completed.")
            connection.execute(
                "INSERT INTO users (username, salt, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (username, salt, password_hash),
            )
            connection.commit()

    def _require_admin(self, actor):
        if (
            not isinstance(actor, dict)
            or actor.get("role") != "admin"
            or not actor.get("username")
            or not self.is_session_valid(
                actor["username"], actor["role"], actor.get("session_version")
            )
        ):
            raise AuthenticationError("An active administrator session is required.")

    def create_user(self, actor, username, password, role="user"):
        self._require_admin(actor)
        username = self._normalize_username(username)
        self._validate_password(password)
        if role not in ("admin", "user"):
            raise AuthenticationError("Choose a valid account role.")
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO users (username, salt, password_hash, role) VALUES (?, ?, ?, ?)",
                    (username, salt, password_hash, role),
                )
                connection.commit()
        except sqlite3.IntegrityError as error:
            raise AuthenticationError("That username is already registered.") from error

    @staticmethod
    def _invitation_hash(token):
        return hashlib.sha256(token.encode("utf-8")).digest()

    def create_invitation(self, actor):
        self._require_admin(actor)
        token = secrets.token_urlsafe(24)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO invitations (token_hash, created_by, expires_at) VALUES (?, ?, ?)",
                (
                    self._invitation_hash(token),
                    actor["username"],
                    time.time() + INVITATION_LIFETIME_SECONDS,
                ),
            )
            connection.commit()
        return token

    def register_user(self, invitation, username, password):
        token = str(invitation or "").strip()
        if not token or len(token) > 128:
            raise AuthenticationError("Enter a valid invitation code from an administrator.")
        username = self._normalize_username(username)
        self._validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                invitation_row = connection.execute(
                    "SELECT expires_at, used_at FROM invitations WHERE token_hash = ?",
                    (self._invitation_hash(token),),
                ).fetchone()
                if (
                    not invitation_row
                    or invitation_row["used_at"] is not None
                    or invitation_row["expires_at"] <= time.time()
                ):
                    raise AuthenticationError(
                        "That invitation code is invalid, expired, or already used."
                    )
                connection.execute(
                    """
                    INSERT INTO users (username, salt, password_hash, role)
                    VALUES (?, ?, ?, 'user')
                    """,
                    (username, salt, password_hash),
                )
                connection.execute(
                    "UPDATE invitations SET used_at = ? WHERE token_hash = ?",
                    (time.time(), self._invitation_hash(token)),
                )
                connection.commit()
        except sqlite3.IntegrityError as error:
            raise AuthenticationError("That username is already registered.") from error

    def authenticate(self, username, password):
        username = self._normalize_username(username)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT username, salt, password_hash, role, enabled, session_version FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            attempt = connection.execute(
                "SELECT failed_count, locked_until FROM login_attempts WHERE username = ?",
                (username,),
            ).fetchone()

        now = time.time()
        if attempt and attempt["locked_until"] > now:
            remaining = max(1, int(attempt["locked_until"] - now + 0.999))
            raise AuthenticationError(
                f"Too many failed sign-in attempts. Try again in {remaining} seconds."
            )

        salt = row["salt"] if row else DUMMY_SALT
        expected_hash = row["password_hash"] if row else self._password_hash(
            "not-a-real-account-password", DUMMY_SALT
        )
        supplied_hash = self._password_hash(str(password or ""), salt)
        valid = hmac.compare_digest(supplied_hash, expected_hash)

        if not row or not valid or not row["enabled"]:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                current_attempt = connection.execute(
                    "SELECT failed_count, locked_until FROM login_attempts WHERE username = ?",
                    (username,),
                ).fetchone()
                if current_attempt and current_attempt["locked_until"] > time.time():
                    remaining = max(1, int(current_attempt["locked_until"] - time.time() + 0.999))
                    raise AuthenticationError(
                        f"Too many failed sign-in attempts. Try again in {remaining} seconds."
                    )
                failed_count = (current_attempt["failed_count"] if current_attempt else 0) + 1
                locked_until = time.time() + LOCKOUT_SECONDS if failed_count >= MAX_FAILED_ATTEMPTS else 0
                connection.execute(
                    """
                    INSERT INTO login_attempts (username, failed_count, locked_until)
                    VALUES (?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        failed_count = excluded.failed_count,
                        locked_until = excluded.locked_until
                    """,
                    (username, failed_count, locked_until),
                )
                connection.commit()
            if locked_until:
                raise AuthenticationError(
                    f"Too many failed sign-in attempts. Try again in {LOCKOUT_SECONDS} seconds."
                )
            raise AuthenticationError("Username or password is incorrect, or the account is disabled.")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current_attempt = connection.execute(
                "SELECT locked_until FROM login_attempts WHERE username = ?", (username,)
            ).fetchone()
            if current_attempt and current_attempt["locked_until"] > time.time():
                remaining = max(1, int(current_attempt["locked_until"] - time.time() + 0.999))
                raise AuthenticationError(
                    f"Too many failed sign-in attempts. Try again in {remaining} seconds."
                )
            connection.execute("DELETE FROM login_attempts WHERE username = ?", (username,))
            connection.commit()
        return {
            "username": row["username"],
            "role": row["role"],
            "session_version": row["session_version"],
        }

    def is_session_valid(self, username, role, session_version):
        username = self._normalize_username(username)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT role, enabled, session_version FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return bool(
            row
            and row["enabled"]
            and row["role"] == role
            and row["session_version"] == session_version
        )

    def list_users(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT username, role, enabled, created_at FROM users ORDER BY username"
            ).fetchall()
        return [dict(row) for row in rows]

    def set_user_enabled(self, actor, username, enabled):
        self._require_admin(actor)
        username = self._normalize_username(username)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT role, enabled FROM users WHERE username = ?", (username,)
            ).fetchone()
            if not row:
                raise AuthenticationError("The selected account no longer exists.")
            if row["role"] == "admin" and row["enabled"] and not enabled:
                other_admin = connection.execute(
                    "SELECT 1 FROM users WHERE role = 'admin' AND enabled = 1 AND username != ? LIMIT 1",
                    (username,),
                ).fetchone()
                if not other_admin:
                    raise AuthenticationError("At least one enabled administrator must remain.")
            connection.execute(
                "UPDATE users SET enabled = ?, session_version = session_version + 1 WHERE username = ?",
                (int(bool(enabled)), username),
            )
            connection.commit()

    def reset_password(self, actor, username, password):
        self._require_admin(actor)
        username = self._normalize_username(username)
        self._validate_password(password)
        salt = secrets.token_bytes(16)
        password_hash = self._password_hash(password, salt)
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE users SET salt = ?, password_hash = ?, session_version = session_version + 1 WHERE username = ?",
                (salt, password_hash, username),
            )
            if cursor.rowcount != 1:
                raise AuthenticationError("The selected account no longer exists.")
            connection.execute("DELETE FROM login_attempts WHERE username = ?", (username,))
            connection.commit()
