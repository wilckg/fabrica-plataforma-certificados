import json
import os
import re
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURSES_JSON_PATH = os.path.join(BASE_DIR, "courses.json")


def clean_text(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_workload(value: str) -> str:
    value = clean_text(value)
    if not value:
        return ""

    # Remove sobras como "SAIBA MAIS"
    value = re.sub(r"\bSAIBA MAIS\b", "", value, flags=re.IGNORECASE)
    value = clean_text(value)
    return value


def convert_js_modal_url(value: str) -> str:
    value = clean_text(value)
    if not value:
        return None

    # Mantém URLs normais como estão
    if value.startswith("http://") or value.startswith("https://"):
        return value

    # Se vier javascript:openModalInfo(...), preserva o original por enquanto.
    # Caso depois você descubra a URL final do detalhe, pode trocar essa lógica.
    return value


def load_courses_from_json() -> list[dict]:
    if not os.path.exists(COURSES_JSON_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {COURSES_JSON_PATH}")

    with open(COURSES_JSON_PATH, "r", encoding="utf-8") as file:
        raw_courses = json.load(file)

    courses = []
    seen_titles = set()

    for item in raw_courses:
        title = clean_text(item.get("nome"))
        description = clean_text(item.get("descricao"))
        workload = normalize_workload(item.get("carga_horaria"))
        details_url = convert_js_modal_url(item.get("detalhe_url"))
        enroll_url = convert_js_modal_url(item.get("inscricao_url"))
        source = "SENAI-SP"

        # Filtra registros ruins/vazios que vieram do JSON
        if not title:
            continue

        invalid_titles = {
            "Aguarde...",
        }

        if title in invalid_titles:
            continue

        if title in seen_titles:
            continue

        # Se a descrição veio muito genérica, usa a área como fallback
        if not description:
            description = clean_text(item.get("area")) or "Curso disponível no catálogo do SENAI."

        # Se ainda não houver link de inscrição, mantém null
        # para o front tratar depois.
        courses.append({
            "title": title,
            "description": description,
            "workload": workload,
            "details_url": details_url,
            "enroll_url": enroll_url,
            "source": source,
            "unit": clean_text(item.get("unidade")),
            "modality": clean_text(item.get("modalidade")),
            "level": clean_text(item.get("nivel")),
            "area": clean_text(item.get("area")),
            "modal_id": item.get("modal_id")
        })
        seen_titles.add(title)

    return courses


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/senai-courses", methods=["GET"])
def senai_courses():
    try:
        courses = load_courses_from_json()
        return jsonify({
            "total": len(courses),
            "courses": courses
        })
    except Exception as e:
        return jsonify({
            "error": "Erro ao carregar cursos do arquivo JSON",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)