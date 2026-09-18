import psycopg
from psycopg.rows import dict_row

DB_URI = "postgresql://postgres:1234@localhost:5432/chatbot"


def get_conn():
    return psycopg.connect(DB_URI, row_factory=dict_row, autocommit=True)


def init_conversations_table():
    """Call once at startup. Creates a small metadata table alongside
    the langgraph checkpoint tables so we can list conversations and
    give them a readable title without touching langgraph's internals."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_conversations (
                thread_id  TEXT PRIMARY KEY,
                title      TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def create_conversation(thread_id: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_conversations (thread_id) VALUES (%s)",
            (thread_id,),
        )


def list_conversations():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT thread_id, title, created_at "
            "FROM chat_conversations ORDER BY created_at DESC"
        ).fetchall()
    return rows
def delete_conversation(thread_id: str):
    """Deletes the conversation's metadata row plus its LangGraph
    checkpoint data (checkpoints, blobs, and pending writes)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
        conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
        conn.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
        conn.execute("DELETE FROM chat_conversations WHERE thread_id = %s", (thread_id,))

def maybe_set_title(thread_id: str, first_message: str):
    """Give the conversation a real title the first time it's used,
    based on the user's first message. Leaves later titles alone."""
    title = first_message.strip().replace("\n", " ")[:50]
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE chat_conversations
            SET title = %s
            WHERE thread_id = %s AND title = 'New Chat'
            """,
            (title, thread_id),
        )