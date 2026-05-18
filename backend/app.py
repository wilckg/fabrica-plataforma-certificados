import os
import re
import hashlib
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada.")
    return psycopg2.connect(DATABASE_URL)


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def only_numbers(value):
    return re.sub(r"\D", "", value or "")


def is_valid_cpf(cpf):
    cpf = only_numbers(cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        total = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digit = ((total * 10) % 11) % 10

        if digit != int(cpf[i]):
            return False

    return True


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def calculate_file_hash(file):
    sha256 = hashlib.sha256()
    file.stream.seek(0)

    for chunk in iter(lambda: file.stream.read(4096), b""):
        sha256.update(chunk)

    file.stream.seek(0)
    return sha256.hexdigest()


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    student_cpf TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'pendente',
                    ai_status TEXT,
                    ai_confidence NUMERIC,
                    ai_analysis TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/db-check", methods=["GET"])
def db_check():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()

        return jsonify({
            "database": "connected",
            "test": result[0]
        }), 200

    except Exception as error:
        return jsonify({
            "database": "error",
            "message": str(error)
        }), 500

@app.route("/api/env-check", methods=["GET"])
def env_check():
    return jsonify({
        "database_url_configured": bool(os.getenv("DATABASE_URL"))
    }), 200

@app.route("/api/submissions", methods=["POST"])
def create_submission():
    student_name = clean_text(request.form.get("student_name"))
    student_cpf = only_numbers(request.form.get("student_cpf"))
    certificate = request.files.get("certificate")

    if not student_name or not student_cpf or not certificate:
        return jsonify({
            "error": "Nome completo, CPF e arquivo são obrigatórios."
        }), 400

    if len(student_name.split()) < 2:
        return jsonify({"error": "Informe o nome completo."}), 400

    if not is_valid_cpf(student_cpf):
        return jsonify({"error": "CPF inválido."}), 400

    if not certificate.filename:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    if not allowed_file(certificate.filename):
        return jsonify({
            "error": "Formato inválido. Envie PDF, PNG, JPG ou JPEG."
        }), 400

    certificate.seek(0, os.SEEK_END)
    file_size = certificate.tell()
    certificate.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({
            "error": "Arquivo muito grande. Limite máximo: 5 MB."
        }), 400

    file_hash = calculate_file_hash(certificate)
    safe_filename = secure_filename(certificate.filename)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, student_name, student_cpf, original_filename, created_at
                FROM submissions
                WHERE file_hash = %s
            """, (file_hash,))

            existing = cur.fetchone()

            if existing:
                return jsonify({
                    "error": "Este certificado já foi enviado anteriormente.",
                    "submission": {
                        "id": existing["id"],
                        "student_name": existing["student_name"],
                        "student_cpf": existing["student_cpf"],
                        "original_filename": existing["original_filename"],
                        "created_at": str(existing["created_at"])
                    }
                }), 409

            cur.execute("""
                INSERT INTO submissions
                (
                    student_name,
                    student_cpf,
                    original_filename,
                    file_hash,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                student_name,
                student_cpf,
                safe_filename,
                file_hash,
                "pendente"
            ))

            new_submission = cur.fetchone()
            conn.commit()

    return jsonify({
        "message": "Certificado enviado com sucesso.",
        "submission_id": new_submission["id"],
        "status": "pendente"
    }), 201


@app.route("/api/submissions", methods=["GET"])
def list_submissions():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    student_name,
                    student_cpf,
                    original_filename,
                    status,
                    ai_status,
                    ai_confidence,
                    ai_analysis,
                    created_at
                FROM submissions
                ORDER BY created_at DESC
            """)

            rows = cur.fetchall()

    return jsonify({
        "submissions": [
            {
                **row,
                "created_at": str(row["created_at"]),
                "ai_confidence": float(row["ai_confidence"]) if row["ai_confidence"] is not None else None
            }
            for row in rows
        ]
    }), 200


try:
    init_db()
except Exception as error:
    print(f"Erro ao inicializar banco: {error}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)