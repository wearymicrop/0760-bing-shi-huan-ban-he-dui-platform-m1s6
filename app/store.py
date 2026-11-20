from contextlib import contextmanager
from pathlib import Path
import sqlite3


@contextmanager
def connection(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute('''CREATE TABLE IF NOT EXISTS shifts(
            id TEXT PRIMARY KEY, source BLOB NOT NULL, bundle TEXT NOT NULL,
            created TEXT NOT NULL)''')
        with db:
            yield db
    finally:
        db.close()


def find(path, run_id):
    with connection(path) as db:
        return db.execute('SELECT source,bundle FROM shifts WHERE id=?', (run_id,)).fetchone()


def save(path, run_id, source, bundle, created):
    with connection(path) as db:
        changed = db.execute('INSERT OR IGNORE INTO shifts VALUES (?,?,?,?)',
                             (run_id, source, bundle, created)).rowcount
        row = db.execute('SELECT bundle FROM shifts WHERE id=?', (run_id,)).fetchone()
    return row[0], not bool(changed)


def history(path):
    with connection(path) as db:
        return db.execute('SELECT id,created FROM shifts ORDER BY created DESC,id LIMIT 50').fetchall()
