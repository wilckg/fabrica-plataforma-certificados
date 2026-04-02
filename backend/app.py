import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SENAI_URL = "https://www.sp.senai.br/cursos/0/tecnologia-da-informacao-e-informatica?unidade=135&modalidade=3&gratuito=1"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def scrape_senai_courses():
    response = requests.get(
        SENAI_URL,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Coleta links úteis da página
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        label = clean_text(a.get_text(" ", strip=True))
        if href:
            if href.startswith("/"):
                href = f"https://www.sp.senai.br{href}"
            links.append({"label": label, "href": href})

    text_lines = [
        clean_text(line)
        for line in soup.get_text("\n", strip=True).splitlines()
        if clean_text(line)
    ]

    courses = []
    seen_titles = set()

    ignore_exact = {
        "Saiba Mais",
        "Inscreva-se",
        "SENAI ONLINE",
        "Cursos",
        "Filtros",
    }

    i = 0
    while i < len(text_lines):
        line = text_lines[i]

        # Heurística: título seguido de descrição e depois "Carga horária:"
        if line in ignore_exact:
            i += 1
            continue

        window = text_lines[i:i+8]
        joined_window = " ".join(window)

        if "Carga horária:" in joined_window:
            title = line
            description = ""
            workload = ""

            for j in range(i + 1, min(i + 8, len(text_lines))):
                current = text_lines[j]

                if current.startswith("Carga horária:"):
                    workload = current.replace("Carga horária:", "").strip()
                    break

                if current not in ignore_exact and not description:
                    description = current

            # filtros simples para evitar blocos falsos
            if (
                title
                and len(title) > 5
                and title.lower() != description.lower()
                and workload
                and title not in seen_titles
            ):
                related_links = []
                for item in links:
                    label = item["label"].lower()
                    href = item["href"]
                    if "curso" in href or "inscrev" in label or "saiba" in label:
                        related_links.append(item)

                details_url = related_links[0]["href"] if related_links else SENAI_URL
                enroll_url = related_links[1]["href"] if len(related_links) > 1 else SENAI_URL

                courses.append({
                    "title": title,
                    "description": description,
                    "workload": workload,
                    "details_url": details_url,
                    "enroll_url": enroll_url,
                    "source": "SENAI-SP"
                })
                seen_titles.add(title)

        i += 1

    # fallback simples caso a heurística principal não monte nada
    if not courses:
        pattern_titles = [
            "Competência Transversal - Lógica de Programação",
            "Desvendando a Blockchain",
            "Desvendando o 5G",
            "Excel Básico",
            "Ética na Inteligência Artificial",
            "FluêncIA - Fundamentos da Inteligência Artificial",
            "Por dentro da Segurança Cibernética",
        ]

        for idx, line in enumerate(text_lines):
            if line in pattern_titles and line not in seen_titles:
                description = ""
                workload = ""

                for j in range(idx + 1, min(idx + 8, len(text_lines))):
                    current = text_lines[j]
                    if current.startswith("Carga horária:"):
                        workload = current.replace("Carga horária:", "").strip()
                        break
                    if current not in ignore_exact and not description:
                        description = current

                courses.append({
                    "title": line,
                    "description": description,
                    "workload": workload,
                    "details_url": SENAI_URL,
                    "enroll_url": SENAI_URL,
                    "source": "SENAI-SP"
                })
                seen_titles.add(line)

    return courses


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/senai-courses", methods=["GET"])
def senai_courses():
    try:
        courses = scrape_senai_courses()
        return jsonify(courses)
    except Exception as e:
        return jsonify({
            "error": "Erro ao buscar cursos do SENAI",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)