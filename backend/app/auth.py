"""
PARAKH - Authentication and secure session layer

Step 2.3:
- Argon2id password hashing
- User registration
- Login verification
- Secure random session tokens
- SHA-256 storage of session tokens
- HttpOnly session cookie helpers
- Session expiration
- Logout
- Current-user lookup

This module uses the SQLite users and sessions tables created by
app.database.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import HTTPException, Request, Response

from pwdlib import PasswordHash

from app.database import get_connection, init_database


# ============================================================
# CONFIGURATION
# ============================================================

SESSION_COOKIE_NAME = "parakh_session"

SESSION_DURATION_HOURS = 8

DEFAULT_ROLE = "INSPECTOR"


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a password using the recommended Argon2id configuration.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return password_hash.hash(
        password
    )


def verify_password(
    password: str,
    stored_hash: str
) -> bool:
    """
    Verify a plain-text password against its stored Argon2id hash.
    """

    if not password or not stored_hash:
        return False

    try:

        return password_hash.verify(
            password,
            stored_hash
        )

    except Exception:

        return False


# ============================================================
# EMAIL HELPERS
# ============================================================

def normalize_email(email: str) -> str:
    """
    Normalize an email address for consistent account lookup.
    """

    return str(
        email or ""
    ).strip().lower()


# ============================================================
# SESSION TOKEN HELPERS
# ============================================================

def _hash_session_token(
    session_token: str
) -> str:
    """
    Store only a SHA-256 hash of the session token in SQLite.

    The raw token is sent only to the user's browser through the
    HttpOnly cookie and is never stored in the database.
    """

    return hashlib.sha256(
        session_token.encode(
            "utf-8"
        )
    ).hexdigest()


def _utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(
        timezone.utc
    )


def _utc_iso(
    value: datetime
) -> str:
    """
    Convert a datetime into an ISO-8601 UTC string.
    """

    return value.astimezone(
        timezone.utc
    ).isoformat()


def _parse_datetime(
    value: str
):
    """
    Parse an ISO timestamp stored in SQLite.
    """

    if not value:
        return None

    try:

        parsed = datetime.fromisoformat(
            value
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except Exception:

        return None


# ============================================================
# USER OPERATIONS
# ============================================================

def get_user_by_email(
    email: str
):
    """
    Find an active or inactive user by normalized email.
    """

    email = normalize_email(
        email
    )

    if not email:
        return None

    init_database()

    with get_connection() as connection:

        return connection.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash,
                role,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE email = ?
            LIMIT 1
            """,
            (
                email,
            )
        ).fetchone()


def get_user_by_id(
    user_id: int
):
    """
    Find a user by database ID.
    """

    if not user_id:
        return None

    init_database()

    with get_connection() as connection:

        return connection.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash,
                role,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (
                user_id,
            )
        ).fetchone()


def create_user(
    name: str,
    email: str,
    password: str,
    role: str = DEFAULT_ROLE
):
    """
    Create a new PARAKH user.

    The plain password is never stored.
    """

    name = str(
        name or ""
    ).strip()

    email = normalize_email(
        email
    )

    password = str(
        password or ""
    )

    role = str(
        role or DEFAULT_ROLE
    ).strip().upper()

    if not name:
        raise ValueError(
            "Name is required."
        )

    if not email:
        raise ValueError(
            "Email is required."
        )

    if len(password) < 6:
        raise ValueError(
            "Password must contain at least 6 characters."
        )

    if not role:
        role = DEFAULT_ROLE

    existing = get_user_by_email(
        email
    )

    if existing is not None:
        raise ValueError(
            "An account with this email already exists."
        )

    now = _utc_iso(
        _utc_now()
    )

    password_hash_value = hash_password(
        password
    )

    init_database()

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash,
                role,
                is_active,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            (
                name,
                email,
                password_hash_value,
                role,
                now,
                now
            )
        )

        connection.commit()

        user_id = cursor.lastrowid

    return get_user_by_id(
        user_id
    )


def authenticate_user(
    email: str,
    password: str
):
    """
    Verify email + password and return the user row.

    Returns None for invalid credentials or inactive accounts.
    """

    user = get_user_by_email(
        email
    )

    if user is None:
        return None

    if not bool(
        user["is_active"]
    ):
        return None

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    return user


# ============================================================
# USER RESPONSE
# ============================================================

def user_to_dict(
    user
):
    """
    Convert a SQLite user row to a safe API response.

    password_hash is intentionally excluded.
    """

    if user is None:
        return None

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "is_active": bool(
            user["is_active"]
        ),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


# ============================================================
# SESSION CREATION
# ============================================================

def create_session(
    user_id: int
):
    """
    Create a secure random session.

    The raw session token is returned once so it can be placed
    into the browser's HttpOnly cookie.

    Only the SHA-256 hash is stored in SQLite.
    """

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    init_database()

    session_token = secrets.token_urlsafe(
        48
    )

    session_token_hash = _hash_session_token(
        session_token
    )

    now = _utc_now()

    expires_at = (
        now
        + timedelta(
            hours=SESSION_DURATION_HOURS
        )
    )

    created_at = _utc_iso(
        now
    )

    expires_at_text = _utc_iso(
        expires_at
    )

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO sessions (
                user_id,
                session_token_hash,
                expires_at,
                created_at,
                last_used_at,
                revoked_at
            )
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (
                user_id,
                session_token_hash,
                expires_at_text,
                created_at,
                created_at
            )
        )

        connection.commit()

    return {
        "token": session_token,
        "expires_at": expires_at_text,
    }


# ============================================================
# SESSION LOOKUP
# ============================================================

def get_user_from_session_token(
    session_token: str
):
    """
    Validate a session token and return the associated active user.

    Expired/revoked/invalid sessions return None.
    """

    if not session_token:
        return None

    init_database()

    token_hash = _hash_session_token(
        session_token
    )

    now = _utc_now()

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                s.id AS session_id,
                s.user_id,
                s.expires_at,
                s.revoked_at,
                u.id,
                u.name,
                u.email,
                u.password_hash,
                u.role,
                u.is_active,
                u.created_at,
                u.updated_at
            FROM sessions s
            INNER JOIN users u
                ON u.id = s.user_id
            WHERE s.session_token_hash = ?
            LIMIT 1
            """,
            (
                token_hash,
            )
        ).fetchone()

        if row is None:
            return None

        if row["revoked_at"] is not None:
            return None

        if not bool(
            row["is_active"]
        ):
            return None

        expires_at = _parse_datetime(
            row["expires_at"]
        )

        if expires_at is None:
            return None

        if expires_at <= now:

            connection.execute(
                """
                UPDATE sessions
                SET revoked_at = ?
                WHERE id = ?
                """,
                (
                    _utc_iso(now),
                    row["session_id"]
                )
            )

            connection.commit()

            return None

        connection.execute(
            """
            UPDATE sessions
            SET last_used_at = ?
            WHERE id = ?
            """,
            (
                _utc_iso(now),
                row["session_id"]
            )
        )

        connection.commit()

        return row


# ============================================================
# REQUEST SESSION
# ============================================================

def get_session_token_from_request(
    request: Request
):
    """
    Read the secure PARAKH session token from the HttpOnly cookie.
    """

    return request.cookies.get(
        SESSION_COOKIE_NAME
    )


def get_current_user(
    request: Request
):
    """
    Return the currently authenticated user.

    Raises HTTP 401 when the request does not contain a valid session.
    """

    session_token = (
        get_session_token_from_request(
            request
        )
    )

    if not session_token:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    user = get_user_from_session_token(
        session_token
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session."
        )

    return user


# ============================================================
# ROLE CHECK
# ============================================================

def require_role(
    request: Request,
    allowed_roles
):
    """
    Require an authenticated user with one of the supplied roles.
    """

    user = get_current_user(
        request
    )

    role = str(
        user["role"] or ""
    ).upper()

    normalized_roles = {
        str(item).upper()
        for item in allowed_roles
    }

    if role not in normalized_roles:

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to perform this action."
        )

    return user


# ============================================================
# SET SESSION COOKIE
# ============================================================

def set_session_cookie(
    response: Response,
    session_token: str,
    expires_at: str
):
    """
    Set the authentication cookie.

    HttpOnly prevents JavaScript from reading the session token.
    SameSite=Lax is used for the local HTTP frontend/backend setup.
    Secure=False is required for the local HTTP development server.
    """

    expires_datetime = _parse_datetime(
        expires_at
    )

    max_age = SESSION_DURATION_HOURS * 60 * 60

    if expires_datetime is not None:

        remaining = int(
            (
                expires_datetime
                - _utc_now()
            ).total_seconds()
        )

        max_age = max(
            0,
            remaining
        )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        expires=max_age,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_session(
    request: Request,
    response: Response
):
    """
    Revoke the current session and clear the browser cookie.
    """

    session_token = (
        get_session_token_from_request(
            request
        )
    )

    if session_token:

        token_hash = _hash_session_token(
            session_token
        )

        now = _utc_iso(
            _utc_now()
        )

        init_database()

        with get_connection() as connection:

            connection.execute(
                """
                UPDATE sessions
                SET revoked_at = ?
                WHERE session_token_hash = ?
                  AND revoked_at IS NULL
                """,
                (
                    now,
                    token_hash
                )
            )

            connection.commit()

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/"
    )


# ============================================================
# SESSION CLEANUP
# ============================================================

def cleanup_expired_sessions():
    """
    Remove expired/revoked sessions from SQLite.

    This can be called periodically by the backend.
    """

    init_database()

    now = _utc_iso(
        _utc_now()
    )

    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM sessions
            WHERE expires_at <= ?
               OR revoked_at IS NOT NULL
            """,
            (
                now,
            )
        )

        connection.commit()
