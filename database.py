import sqlite3
import os

DATABASE_NAME = 'client_management.db'

def create_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create clients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        document_type TEXT, -- PAN, GST, ITRs, etc.
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)

    # Create reminders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        due_date TEXT NOT NULL,
        reminder_time TEXT, -- Added reminder time
        frequency TEXT,      -- Added frequency
        is_completed BOOLEAN DEFAULT FALSE, -- Added completion status
        last_sent_at DATETIME,             -- Added tracking for last sent email
        description TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)

    # Add columns if they don't exist (for schema evolution)
    cursor.execute("PRAGMA table_info(reminders)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'reminder_time' not in columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN reminder_time TEXT")
    if 'frequency' not in columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN frequency TEXT")
    if 'is_completed' not in columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN is_completed BOOLEAN DEFAULT FALSE")
    if 'last_sent_at' not in columns:
        cursor.execute("ALTER TABLE reminders ADD COLUMN last_sent_at DATETIME")

    conn.commit()
    conn.close()

def get_all_clients():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, created_at FROM clients")
    clients = cursor.fetchall()
    conn.close()
    return clients

def get_client_by_id(client_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, created_at FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    conn.close()
    return client

def add_client(name, email, phone):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clients (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
    client_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return client_id

def add_document(client_id, filename, filepath, document_type):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO documents (client_id, filename, filepath, document_type) VALUES (?, ?, ?, ?)", (client_id, filename, filepath, document_type))
    document_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return document_id

def get_documents_by_client(client_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, client_id, filename, filepath, document_type, uploaded_at FROM documents WHERE client_id = ?", (client_id,))
    documents = cursor.fetchall()
    conn.close()
    return documents

def add_reminder(client_id, due_date, reminder_time, frequency, description):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (client_id, due_date, reminder_time, frequency, description) VALUES (?, ?, ?, ?, ?)",
        (client_id, due_date, reminder_time, frequency, description),
    )
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id

def get_reminders(client_id=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if client_id:
        cursor.execute("SELECT id, client_id, due_date, description, created_at FROM reminders WHERE client_id = ? ORDER BY due_date", (client_id,))
    else:
        cursor.execute("SELECT id, client_id, due_date, description, created_at FROM reminders ORDER BY due_date")
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def update_reminder_last_sent(reminder_id, sent_at_datetime):
    """Updates the last_sent_at timestamp for a reminder."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        # Convert datetime object to ISO 8601 string format for storage
        sent_at_str = sent_at_datetime.isoformat()
        cursor.execute("UPDATE reminders SET last_sent_at = ? WHERE id = ?", (sent_at_str, reminder_id))
        conn.commit()
        # print(f"Updated last_sent_at for reminder {reminder_id}") # Use logging instead
    except sqlite3.Error as e:
        # print(f"Database error updating last_sent_at for reminder {reminder_id}: {e}") # Use logging instead
        conn.rollback() # Rollback changes on error
        raise # Re-raise the exception so the caller knows about the failure
    finally:
        conn.close()

def mark_reminder_completed(reminder_id):
    """Marks a reminder as completed."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE reminders SET is_completed = TRUE WHERE id = ?", (reminder_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    # This will ensure the table schema is up-to-date when run directly
    # Note: ALTER TABLE commands might be needed if the schema changes after initial creation
    # For simplicity here, we assume create_database handles IF NOT EXISTS correctly.
    # In a production scenario, use migration tools (like Alembic for SQLAlchemy).
    create_database()
    print(f"Database '{DATABASE_NAME}' schema checked/created.")