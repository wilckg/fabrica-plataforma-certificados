import os
import re
import json
import hashlib

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from google import genai
from google.genai import types


app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ALLOWED_EXTENSIONS = {"pdf"}
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


def calculate_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()


def parse_json_response(text):
    if not text:
        return None

    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def mask_cpf(cpf):
    cpf = only_numbers(cpf)

    if len(cpf) != 11:
        return "***.***.***-**"

    return f"{cpf[:3]}.***.***-{cpf[-2:]}"

def update_student_ranking(cur, student_cpf, student_name, ai_score, ai_confidence):
    cur.execute("""
        INSERT INTO student_ranking (
            student_cpf,
            student_name,
            valid_certificates,
            total_score,
            average_confidence,
            last_submission
        )
        VALUES (%s, %s, 1, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (student_cpf)
        DO UPDATE SET
            student_name = EXCLUDED.student_name,
            valid_certificates = student_ranking.valid_certificates + 1,
            total_score = student_ranking.total_score + EXCLUDED.total_score,
            average_confidence =
                (
                    (student_ranking.average_confidence * student_ranking.valid_certificates)
                    + EXCLUDED.average_confidence
                ) / (student_ranking.valid_certificates + 1),
            last_submission = CURRENT_TIMESTAMP
    """, (
        student_cpf,
        student_name,
        ai_score,
        ai_confidence
    ))

def analyze_certificate_with_gemini(pdf_bytes, student_name, student_cpf):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Você é um agente inteligente de validação de certificados do SENAI.

Analise o PDF enviado e retorne APENAS JSON válido, sem markdown.

Dados informados pelo aluno:
- Nome completo: {student_name}
- CPF: {student_cpf}

Objetivo:
Verificar se o documento parece ser um certificado do SENAI e se deve contar para o ranking.

Critérios:
1. Verifique se parece ser um certificado.
2. Verifique se menciona SENAI, Departamento Regional de São Paulo ou Escola SENAI.
3. Extraia o nome do aluno no certificado.
4. Extraia o nome do curso.
5. Extraia carga horária.
6. Extraia período, data de conclusão ou data de emissão.
7. Verifique se há assinatura, diretor ou responsável.
8. Verifique se há link de autenticação, QR Code ou código de validação.
9. Verifique se o nome informado pelo aluno parece bater com o nome do certificado.
10. Gere uma pontuação auxiliar de 0 a 100.

Regras para ranking:
- Só deve contar no ranking se parecer certificado SENAI e tiver dados suficientes.
- Se for suspeito, incompleto demais ou não for certificado, ranking_should_count deve ser false.
- A pontuação é auxiliar. O ranking principal será pela quantidade de certificados aceitos.

Regras de score:
- 0: não é certificado ou documento ilegível
- 30: parece certificado, mas não é SENAI
- 50: parece SENAI, mas está incompleto
- 70: certificado SENAI com dados principais
- 90: certificado SENAI com link/código de autenticação
- 100: certificado SENAI muito consistente, com link/código e dados completos

Importante:
Não afirme que é oficialmente autêntico.
Use "aparentemente consistente" quando fizer sentido.
A autenticação oficial só pode ser confirmada por consulta a fonte oficial externa.

Formato obrigatório:
{{
  "is_certificate": true,
  "appears_to_be_senai": true,
  "student_name_in_pdf": "",
  "student_name_matches": true,
  "course_name": "",
  "workload": "",
  "completion_period": "",
  "issue_date": "",
  "school_or_unit": "",
  "auth_link_found": true,
  "auth_link": "",
  "auth_code": "",
  "signature_found": true,
  "ai_status": "aparentemente_valido",
  "confidence": 0.95,
  "score": 90,
  "summary": "",
  "suspicious_elements": [],
  "missing_elements": [],
  "ranking_should_count": true
}}

Valores possíveis para ai_status:
- aparentemente_valido
- incompleto
- suspeito
- nao_e_certificado
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf"
            ),
            prompt
        ],
    )

    result = parse_json_response(response.text)

    if not result:
        return {
            "is_certificate": False,
            "appears_to_be_senai": False,
            "student_name_in_pdf": "",
            "student_name_matches": False,
            "course_name": "",
            "workload": "",
            "completion_period": "",
            "issue_date": "",
            "school_or_unit": "",
            "auth_link_found": False,
            "auth_link": "",
            "auth_code": "",
            "signature_found": False,
            "ai_status": "erro_analise",
            "confidence": 0,
            "score": 0,
            "summary": "A IA não retornou JSON válido.",
            "suspicious_elements": ["Resposta inválida da IA"],
            "missing_elements": [],
            "ranking_should_count": False
        }

    return result


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
                    ai_score INTEGER DEFAULT 0,
                    ai_analysis JSONB,

                    ranking_should_count BOOLEAN DEFAULT FALSE,

                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_student_cpf
                ON submissions(student_cpf)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_ranking
                ON submissions(ranking_should_count)
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


@app.route("/api/gemini-check", methods=["GET"])
def gemini_check():
    return jsonify({
        "gemini_key_configured": bool(GEMINI_API_KEY)
    }), 200


@app.route("/api/submissions", methods=["POST"])
def create_submission():
    student_name = clean_text(request.form.get("student_name"))
    student_cpf = only_numbers(request.form.get("student_cpf"))
    certificate = request.files.get("certificate")

    if not student_name or not student_cpf or not certificate:
        return jsonify({
            "error": "Nome completo, CPF e certificado são obrigatórios."
        }), 400

    if len(student_name.split()) < 2:
        return jsonify({
            "error": "Informe o nome completo."
        }), 400

    if not is_valid_cpf(student_cpf):
        return jsonify({
            "error": "CPF inválido."
        }), 400

    if not certificate.filename:
        return jsonify({
            "error": "Nenhum arquivo enviado."
        }), 400

    if not allowed_file(certificate.filename):
        return jsonify({
            "error": "Formato inválido. Envie apenas PDF."
        }), 400

    pdf_bytes = certificate.read()
    file_size = len(pdf_bytes)

    if file_size > MAX_FILE_SIZE:
        return jsonify({
            "error": "Arquivo muito grande. Limite máximo: 5 MB."
        }), 400

    file_hash = calculate_file_hash(pdf_bytes)
    safe_filename = secure_filename(certificate.filename)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    student_name,
                    student_cpf,
                    original_filename,
                    created_at
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

    try:
        ai_result = analyze_certificate_with_gemini(
            pdf_bytes=pdf_bytes,
            student_name=student_name,
            student_cpf=student_cpf
        )
    except Exception as error:
        ai_result = {
            "is_certificate": False,
            "appears_to_be_senai": False,
            "student_name_in_pdf": "",
            "student_name_matches": False,
            "course_name": "",
            "workload": "",
            "completion_period": "",
            "issue_date": "",
            "school_or_unit": "",
            "auth_link_found": False,
            "auth_link": "",
            "auth_code": "",
            "signature_found": False,
            "ai_status": "erro_analise",
            "confidence": 0,
            "score": 0,
            "summary": f"Erro ao analisar com Gemini: {str(error)}",
            "suspicious_elements": ["Falha na chamada da IA"],
            "missing_elements": [],
            "ranking_should_count": False
        }

    ai_status = ai_result.get("ai_status", "pendente")
    ai_confidence = float(ai_result.get("confidence", 0) or 0)
    ai_score = int(ai_result.get("score", 0) or 0)
    ranking_should_count = bool(ai_result.get("ranking_should_count", False))

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO submissions
                (
                    student_name,
                    student_cpf,
                    original_filename,
                    file_hash,
                    status,
                    ai_status,
                    ai_confidence,
                    ai_score,
                    ai_analysis,
                    ranking_should_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                student_name,
                student_cpf,
                safe_filename,
                file_hash,
                "analisado",
                ai_status,
                ai_confidence,
                ai_score,
                json.dumps(ai_result, ensure_ascii=False),
                ranking_should_count
            ))

            new_submission = cur.fetchone()

            if ranking_should_count:
                update_student_ranking(
                    cur=cur,
                    student_cpf=student_cpf,
                    student_name=student_name,
                    ai_score=ai_score,
                    ai_confidence=ai_confidence
                )

            conn.commit()

    return jsonify({
        "message": "Certificado enviado e analisado com sucesso.",
        "submission_id": new_submission["id"],
        "status": "analisado",
        "ranking_should_count": ranking_should_count,
        "ai_status": ai_status,
        "ai_confidence": ai_confidence,
        "ai_score": ai_score,
        "ai_analysis": ai_result,
        "created_at": str(new_submission["created_at"])
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
                    file_hash,
                    status,
                    ai_status,
                    ai_confidence,
                    ai_score,
                    ranking_should_count,
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


@app.route("/api/ranking", methods=["GET"])
def ranking():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))

    if page < 1:
        page = 1

    if limit < 1 or limit > 50:
        limit = 10

    offset = (page - 1) * limit

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS total FROM student_ranking")
            total = cur.fetchone()["total"]

            cur.execute("""
                SELECT
                    student_name,
                    student_cpf,
                    valid_certificates,
                    total_score,
                    average_confidence,
                    last_submission
                FROM student_ranking
                ORDER BY
                    valid_certificates DESC,
                    total_score DESC,
                    average_confidence DESC,
                    last_submission ASC
                LIMIT %s OFFSET %s
            """, (limit, offset))

            rows = cur.fetchall()

    ranking_data = []

    for index, row in enumerate(rows, start=offset + 1):
        ranking_data.append({
            "position": index,
            "student_name": row["student_name"],
            "student_cpf_masked": mask_cpf(row["student_cpf"]),
            "valid_certificates": int(row["valid_certificates"] or 0),
            "total_score": int(row["total_score"] or 0),
            "average_confidence": float(row["average_confidence"] or 0),
            "last_submission": str(row["last_submission"])
        })

    return jsonify({
        "ranking": ranking_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    }), 200


try:
    init_db()
except Exception as error:
    print(f"Erro ao inicializar banco: {error}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)