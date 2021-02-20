import asyncio
from dataclasses import dataclass
import datetime
import enum
import uuid
import random

from sqlitedict import SqliteDict

DATABASE_FILE = "./my_db.sqlite"


class SessionState(enum.Enum):
    """A SessionStage describes the possible states of a session.

    1. When a session is created, it is WAITING_ON_START for the user to enter
    an email.
    2. When we send an email it goes into WAITING_ON_CODE and we wait for the
    user to enter the code.
    3. When the session is verified, it goes into VERIFIED and can be deleted.
    """
    WAITING_ON_START = enum.auto()
    WAITING_ON_CODE = enum.auto()
    VERIFIED = enum.auto()


@dataclass
class Session():
    """Class for keeping track of a verification session."""
    user_id: int
    guild_id: int
    discord_name: str
    verification_code: str
    timestamp: datetime.datetime
    state: SessionState = SessionState.WAITING_ON_START
    remaining_attempts: int = 5


def _new_fake_session() -> str:
    """Start a new fake session for testing.

    This session will never get verified by the bot."""
    session_id = "123"

    with SqliteDict(DATABASE_FILE) as db:
        db[session_id] = Session(
            user_id=0,
            guild_id=0,
            discord_name="Testing#123",
            verification_code="-420",
            timestamp=datetime.datetime.now(),
        )
        db.commit()
    return session_id


def new_session(user_id: int, guild_id: int, discord_name: str) -> str:
    """Start a new session for a user in a guild and return the id for the session."""
    session_id = str(uuid.uuid4())
    verification_code = str(random.randint(10000000, 99999999))

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


def set_email_sent(session_id: str):
    """Transition a session into the WAITING_ON_CODE state."""
    with SqliteDict(DATABASE_FILE) as db:
        try:
            session = db[session_id]
        except KeyError:
            # TODO: handle this error
            return
        session.state = SessionState.WAITING_ON_CODE
        db[session_id] = session
        db.commit()


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

        if attempted_code == expected_code:
            session.state = SessionState.VERIFIED
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
            if not session.state is SessionState.VERIFIED or _expired(
                    session, expiry_seconds):
                continue
            # TODO: make this testing part cleaner
            if session.verification_code == "-420":
                continue
            yield session_id, session
