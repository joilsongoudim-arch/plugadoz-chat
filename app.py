import os
import sqlite3
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    request,
    jsonify,
    session,
    render_template,
    send_from_directory,
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "plugadoz.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)


ALLOWED_IMAGES = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

ALLOWED_AUDIO = {
    "mp3",
    "wav",
    "ogg",
    "webm",
    "m4a"
}


def db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = db()

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar TEXT,
            created_at TEXT NOT NULL,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL DEFAULT 'private',
            name TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS conversation_members (
            conversation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL,
            PRIMARY KEY(conversation_id, user_id),
            FOREIGN KEY(conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'text',
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conversation
        ON messages(conversation_id);

        CREATE INDEX IF NOT EXISTS idx_members_user
        ON conversation_members(user_id);

        CREATE INDEX IF NOT EXISTS idx_status_expiry
        ON statuses(expires_at);
        """
    )

    connection.commit()
    connection.close()


def now():
    return datetime.now(timezone.utc).isoformat()


def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    connection = db()

    user = connection.execute(
        """
        SELECT id, username, display_name, avatar, created_at, last_seen
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    return user


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({
                "ok": False,
                "error": "Não autenticado."
            }), 401

        return function(*args, **kwargs)

    return wrapper


def valid_extension(filename, allowed):
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in allowed


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip().lower()

    display_name = str(
        data.get("display_name", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if len(username) < 3:
        return jsonify({
            "ok": False,
            "error": "Usuário precisa ter pelo menos 3 caracteres."
        }), 400

    if len(password) < 6:
        return jsonify({
            "ok": False,
            "error": "A senha precisa ter pelo menos 6 caracteres."
        }), 400

    if not display_name:
        display_name = username

    if len(username) > 40 or len(display_name) > 80:
        return jsonify({
            "ok": False,
            "error": "Nome muito grande."
        }), 400

    connection = db()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                display_name,
                created_at,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                username,
                generate_password_hash(password),
                display_name,
                now(),
                now()
            )
        )

        user_id = cursor.lastrowid

        connection.commit()

    except sqlite3.IntegrityError:
        connection.close()

        return jsonify({
            "ok": False,
            "error": "Esse usuário já existe."
        }), 409

    connection.close()

    session["user_id"] = user_id

    return jsonify({
        "ok": True,
        "user": {
            "id": user_id,
            "username": username,
            "display_name": display_name
        }
    })


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    connection = db()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    if not user:
        connection.close()

        return jsonify({
            "ok": False,
            "error": "Usuário ou senha incorretos."
        }), 401

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        connection.close()

        return jsonify({
            "ok": False,
            "error": "Usuário ou senha incorretos."
        }), 401

    connection.execute(
        """
        UPDATE users
        SET last_seen = ?
        WHERE id = ?
        """,
        (now(), user["id"])
    )

    connection.commit()
    connection.close()

    session["user_id"] = user["id"]

    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "avatar": user["avatar"]
        }
    })


@app.post("/api/logout")
def logout():
    session.clear()

    return jsonify({
        "ok": True
    })


@app.get("/api/me")
def me():
    user = current_user()

    if not user:
        return jsonify({
            "ok": False,
            "user": None
        })

    return jsonify({
        "ok": True,
        "user": dict(user)
    })


@app.get("/api/users")
@login_required
def users():
    user = current_user()

    search = str(
        request.args.get("q", "")
    ).strip().lower()

    connection = db()

    if search:
        rows = connection.execute(
            """
            SELECT id, username, display_name, avatar, last_seen
            FROM users
            WHERE id != ?
            AND (
                username LIKE ?
                OR display_name LIKE ?
            )
            ORDER BY display_name
            LIMIT 50
            """,
            (
                user["id"],
                f"%{search}%",
                f"%{search}%"
            )
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT id, username, display_name, avatar, last_seen
            FROM users
            WHERE id != ?
            ORDER BY display_name
            LIMIT 50
            """,
            (user["id"],)
        ).fetchall()

    connection.close()

    return jsonify({
        "ok": True,
        "users": [dict(row) for row in rows]
    })


@app.post("/api/conversations/private")
@login_required
def create_private_conversation():
    user = current_user()

    data = request.get_json(silent=True) or {}

    other_id = data.get("user_id")

    try:
        other_id = int(other_id)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "error": "Usuário inválido."
        }), 400

    if other_id == user["id"]:
        return jsonify({
            "ok": False,
            "error": "Você não pode conversar consigo mesmo."
        }), 400

    connection = db()

    other = connection.execute(
        """
        SELECT id
        FROM users
        WHERE id = ?
        """,
        (other_id,)
    ).fetchone()

    if not other:
        connection.close()

        return jsonify({
            "ok": False,
            "error": "Usuário não encontrado."
        }), 404

    existing = connection.execute(
        """
        SELECT c.id
        FROM conversations c
        JOIN conversation_members m1
            ON m1.conversation_id = c.id
        JOIN conversation_members m2
            ON m2.conversation_id = c.id
        WHERE c.kind = 'private'
        AND m1.user_id = ?
        AND m2.user_id = ?
        LIMIT 1
        """,
        (user["id"], other_id)
    ).fetchone()

    if existing:
        conversation_id = existing["id"]

    else:
        cursor = connection.execute(
            """
            INSERT INTO conversations (
                kind,
                created_by,
                created_at
            )
            VALUES ('private', ?, ?)
            """,
            (user["id"], now())
        )

        conversation_id = cursor.lastrowid

        timestamp = now()

        connection.execute(
            """
            INSERT INTO conversation_members (
                conversation_id,
                user_id,
                joined_at
            )
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                user["id"],
                timestamp
            )
        )

        connection.execute(
            """
            INSERT INTO conversation_members (
                conversation_id,
                user_id,
                joined_at
            )
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                other_id,
                timestamp
            )
        )

        connection.commit()

    connection.close()

    return jsonify({
        "ok": True,
        "conversation_id": conversation_id
    })


@app.post("/api/conversations/group")
@login_required
def create_group():
    user = current_user()

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    member_ids = data.get("member_ids", [])

    if not name:
        return jsonify({
            "ok": False,
            "error": "Informe o nome do grupo."
        }), 400

    if not isinstance(member_ids, list):
        member_ids = []

    clean_ids = set()

    for value in member_ids:
        try:
            clean_ids.add(int(value))
        except (TypeError, ValueError):
            pass

    clean_ids.add(user["id"])

    connection = db()

    cursor = connection.execute(
        """
        INSERT INTO conversations (
            kind,
            name,
            created_by,
            created_at
        )
        VALUES ('group', ?, ?, ?)
        """,
        (
            name,
            user["id"],
            now()
        )
    )

    conversation_id = cursor.lastrowid

    timestamp = now()

    for member_id in clean_ids:
        exists = connection.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            """,
            (member_id,)
        ).fetchone()

        if exists:
            connection.execute(
                """
                INSERT OR IGNORE INTO conversation_members (
                    conversation_id,
                    user_id,
                    joined_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    conversation_id,
                    member_id,
                    timestamp
                )
            )

    connection.commit()
    connection.close()

    return jsonify({
        "ok": True,
        "conversation_id": conversation_id
    })


@app.get("/api/conversations")
@login_required
def conversations():
    user = current_user()

    connection = db()

    rows = connection.execute(
        """
        SELECT
            c.id,
            c.kind,
            c.name,
            c.created_at,

            (
                SELECT m.content
                FROM messages m
                WHERE m.conversation_id = c.id
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message,

            (
                SELECT m.created_at
                FROM messages m
                WHERE m.conversation_id = c.id
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message_at

        FROM conversations c

        JOIN conversation_members cm
            ON cm.conversation_id = c.id

        WHERE cm.user_id = ?

        ORDER BY
            COALESCE(last_message_at, c.created_at) DESC
        """,
        (user["id"],)
    ).fetchall()

    result = []

    for row in rows:
        item = dict(row)

        if row["kind"] == "private":
            other = connection.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.display_name,
                    u.avatar,
                    u.last_seen
                FROM conversation_members cm
                JOIN users u
                    ON u.id = cm.user_id
                WHERE cm.conversation_id = ?
                AND u.id != ?
                LIMIT 1
                """,
                (
                    row["id"],
                    user["id"]
                )
            ).fetchone()

            item["other_user"] = (
                dict(other)
                if other
                else None
            )

        else:
            item["other_user"] = None

        result.append(item)

    connection.close()

    return jsonify({
        "ok": True,
        "conversations": result
    })


@app.get("/api/conversations/<int:conversation_id>/messages")
@login_required
def conversation_messages(conversation_id):
    user = current_user()

    connection = db()

    member = connection.execute(
        """
        SELECT 1
        FROM conversation_members
        WHERE conversation_id = ?
        AND user_id = ?
        """,
        (
            conversation_id,
            user["id"]
        )
    ).fetchone()

    if not member:
        connection.close()

        return jsonify({
            "ok": False,
            "error": "Você não pertence a esta conversa."
        }), 403

    rows = connection.execute(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.user_id,
            u.username,
            u.display_name,
            m.message_type,
            m.content,
            m.created_at
        FROM messages m
        JOIN users u
            ON u.id = m.user_id
        WHERE m.conversation_id = ?
        ORDER BY m.id ASC
        LIMIT 500
        """,
        (conversation_id,)
    ).fetchall()

    connection.close()

    return jsonify({
        "ok": True,
        "messages": [dict(row) for row in rows]
    })


@app.post("/api/upload")
@login_required
def upload():
    if "file" not in request.files:
        return jsonify({
            "ok": False,
            "error": "Nenhum arquivo enviado."
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "ok": False,
            "error": "Arquivo inválido."
        }), 400

    filename = secure_filename(file.filename)

    is_image = valid_extension(
        filename,
        ALLOWED_IMAGES
    )

    is_audio = valid_extension(
        filename,
        ALLOWED_AUDIO
    )

    if not is_image and not is_audio:
        return jsonify({
            "ok": False,
            "error": "Tipo de arquivo não permitido."
        }), 400

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    unique_name = (
        secrets.token_hex(16)
        + "."
        + extension
    )

    path = os.path.join(
        UPLOAD_DIR,
        unique_name
    )

    file.save(path)

    message_type = (
        "image"
        if is_image
        else "audio"
    )

    return jsonify({
        "ok": True,
        "type": message_type,
        "url": "/uploads/" + unique_name
    })


@app.get("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


@app.post("/api/status")
@login_required
def create_status():
    user = current_user()

    data = request.get_json(silent=True) or {}

    content = str(
        data.get("content", "")
    ).strip()

    if not content:
        return jsonify({
            "ok": False,
            "error": "Status vazio."
        }), 400

    created = datetime.now(timezone.utc)

    expires = created.timestamp() + (
        24 * 60 * 60
    )

    expires_at = datetime.fromtimestamp(
        expires,
        timezone.utc
    ).isoformat()

    connection = db()

    cursor = connection.execute(
        """
        INSERT INTO statuses (
            user_id,
            content,
            created_at,
            expires_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user["id"],
            content,
            created.isoformat(),
            expires_at
        )
    )

    connection.commit()

    status_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "ok": True,
        "status_id": status_id
    })


@app.get("/api/status")
@login_required
def statuses():
    connection = db()

    current = now()

    rows = connection.execute(
        """
        SELECT
            s.id,
            s.user_id,
            u.username,
            u.display_name,
            u.avatar,
            s.content,
            s.created_at,
            s.expires_at
        FROM statuses s
        JOIN users u
            ON u.id = s.user_id
        WHERE s.expires_at > ?
        ORDER BY s.id DESC
        """,
        (current,)
    ).fetchall()

    connection.execute(
        """
        DELETE FROM statuses
        WHERE expires_at <= ?
        """,
        (current,)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "ok": True,
        "statuses": [dict(row) for row in rows]
    })


@socketio.on("join")
def socke
