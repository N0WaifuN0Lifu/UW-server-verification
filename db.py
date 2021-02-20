import asyncio
from dataclasses import dataclass
import datetime
import uuid
import random

from sqlitedict import SqliteDict

DATABASE_FILE = "./my_db.sqlite"


@dataclass
class Session():
    """Class for keeping track of a verification session."""
    user_id: int
    guild_id: int
    discord_name: str
    verification_code: str
    timestamp: datetime.datetime
    is_email_verified: bool = False
    remaining_attempts: int = 5


def new_session(user_id: int, guild_id: int, discord_name: str) -> str:
    """Start a new session for a user in a guild and return the id for the session."""
    session_id = str(uuid.uuid4())
    verification_code = random.randint(10000000, 99999999)

    with SqliteDict(DATABASE_FILE) as db:
        db[session_id] = Session(
            user_id=user_id,
            guild_id=guild_id,
            discord_name=discord_name,
            verification_code=verification_code,
            timestamp=datetime.datetime.now(),
        )
        db.commit()
    return session_id


def peek_attempts(session_id: str):
    """Return the number of remaining attempts for a session."""
    with SqliteDict(DATABASE_FILE) as db:
        try:
            return db[session_id].remaining_attempts
        except KeyError:
            return None


def session(session_id: str) -> Session:
    """Return the session for the id."""
    with SqliteDict(DATABASE_FILE) as db:
        try:
            return db[session_id]
        except KeyError:
            return None


def verify(session_id: str, attempted_code: str):
    """Verify a user using an attempted verification code.
    
    Returns:
        True if the verification was successful
        An integer indicating the number of attempts remaining
        None if the session doesn't exist
    """
    with SqliteDict(DATABASE_FILE) as db:
        try:
            session = db[session_id]
        except KeyError:
            return None

        expected_code = session.verification_code

        if attempted_code == str(expected_code):
            session.is_email_verified = True
            db[session_id] = session
            db.commit()
            return True
        else:
            session.remaining_attempts -= 1
            if session.remaining_attempts == 0:
                del db[session_id]
            else:
                db[session_id] = session

            db.commit()
            return session.remaining_attempts


def delete_session(session_id: str):
    """Remove a session from the db."""
    with SqliteDict(DATABASE_FILE) as db:
        try:
            del db[session_id]
            db.commit()
        except KeyError:
            print(f"Attempted to delete nonexistent session {session_id}")
            pass


def _expired(session: str, expiry_seconds: int) -> bool:
    """Determine if a Session is expired."""
    # TODO: configurable expiry
    delta = datetime.datetime.now() - session.timestamp
    return delta.total_seconds() > expiry_seconds


async def collect_garbage(expiry_seconds: int):
    """Delete expired sessions."""
    with SqliteDict(DATABASE_FILE) as db:
        for session_id in tuple(db.keys()):
            if _expired(db[session_id], expiry_seconds):
                try:
                    del db[session_id]
                    db.commit()
                except KeyError:
                    pass
            await asyncio.sleep(0)


async def verified_user_ids(expiry_seconds: int):
    with SqliteDict(DATABASE_FILE, flag='r') as db:
        for session_id, session in db.items():
            if not session.is_email_verified or _expired(
                    session, expiry_seconds):
                continue
            yield session_id, session
