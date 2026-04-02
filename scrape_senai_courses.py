# scrape_senai_courses.py
# Python 3.10+
#
# Instalação:
#   pip install playwright
#   playwright install chromium
#
# Uso:
#   python scrape_senai_courses.py
#
# Saída:
#   courses.json
#   courses.csv

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://www.sp.senai.br"
START_URL = (
    "https://www.sp.senai.br/cursos/0/tecnologia-da-informacao-e-informatica"
    "?unidade=135&modalidade=3&gratuito=1"
)

OUTPUT_JSON = "courses.json"
OUTPUT_CSV = "courses.csv"


@dataclass
class Course:
    nome: str
    descricao: str
    detalhe_url: Optional[str]
    inscricao_url: Optional[str]
    carga_horaria: Optional[str]
    unidade: Optional[str]
    modalidade: Optional[str]
    nivel: Optional[str]
    area: Optional[str]
    modal_id: Optional[str] = None


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def safe_url(base: str, href: Optional[str]) -> Optional[str]:
    if not href:
        return None

    href = href.strip()

    # não tenta converter pseudo-links javascript em URL real
    if href.lower().startswith("javascript:"):
        return href

    return urljoin(base, href)

def extract_modal_id(js_href: Optional[str]) -> Optional[str]:
    if not js_href:
        return None

    match = re.search(r"openModalInfo\\([^,]+,\\s*(\\d+)\\)", js_href)
    if match:
        return match.group(1)

    return None

def unique_key(course: Course) -> str:
    # prioriza link de detalhe, depois link de inscrição, depois nome
    return (
        (course.detalhe_url or "").strip().lower()
        or (course.inscricao_url or "").strip().lower()
        or course.nome.strip().lower()
    )


def try_extract_course_cards(page) -> List[Course]:
    """
    Extrai cursos da página atual usando JS no DOM do navegador.
    A estratégia é procurar títulos, subir para um container pai plausível
    e capturar os links 'Saiba Mais' e 'Inscreva-se' dentro desse bloco.
    """
    raw_items = page.evaluate(
        """
        () => {
          const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();

          // Títulos observados no HTML parseado aparecem em <h5>, mas
          // aqui tornamos tolerante para mudanças de nível.
          const titleNodes = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
            .filter(el => {
              const txt = norm(el.innerText);
              if (!txt) return false;
              if (txt.length < 4) return false;

              // Evita cabeçalhos da página/filtros
              const blocked = [
                'filtro', 'área', 'nível', 'modalidade', 'turno',
                'senai - cursos', 'senai santana de parnaíba'
              ];
              const lower = txt.toLowerCase();
              if (blocked.some(x => lower === x || lower.includes(x))) return false;

              // Mantém candidatos mais parecidos com nome de curso
              return true;
            });

          const results = [];

          for (const titleEl of titleNodes) {
            const nome = norm(titleEl.innerText);
            if (!nome) continue;

            // Sobe alguns níveis procurando um container que tenha os botões relevantes
            let container = titleEl;
            for (let i = 0; i < 6 && container; i++) {
              const txt = norm(container.innerText).toLowerCase();
              if (txt.includes('inscreva-se') || txt.includes('saiba mais')) {
                break;
              }
              container = container.parentElement;
            }
            if (!container) continue;

            const anchors = Array.from(container.querySelectorAll('a[href]'));
            const saibaMais = anchors.find(a => /saiba\\s+mais/i.test(norm(a.innerText)));
            const inscreva = anchors.find(a => /inscreva-se/i.test(norm(a.innerText)));

            const text = norm(container.innerText);

            // descrição: pega o primeiro parágrafo que não seja nome, carga horária ou rótulos
            let descricao = '';
            const descCandidates = Array.from(container.querySelectorAll('p, div, span'))
              .map(el => norm(el.innerText))
              .filter(Boolean)
              .filter(t => t !== nome)
              .filter(t => !/^carga horária:/i.test(t))
              .filter(t => !/^saiba mais$/i.test(t))
              .filter(t => !/^inscreva-se$/i.test(t))
              .filter(t => !/^senai online$/i.test(t))
              .filter(t => t.length > 30);

            if (descCandidates.length) {
              descricao = descCandidates[0];
            } else {
              // fallback: tenta extrair do texto bruto do container
              const parts = text.split(/carga\\s+horária:/i)[0].split(nome);
              if (parts.length > 1) {
                descricao = norm(parts[1]);
              }
            }

            const cargaMatch = text.match(/Carga\\s*hor[aá]ria:\\s*([^\\n]+)/i);
            const carga_horaria = cargaMatch ? norm(cargaMatch[1]) : null;

            // tenta inferir metadados do texto do card
            const modalidade = /a dist[aâ]ncia/i.test(text) ? 'A Distância' :
                               /presencial/i.test(text) ? 'Presencial' : null;

            const nivel = /cursos livres/i.test(text) ? 'Cursos Livres' :
                          /cursos t[eé]cnicos/i.test(text) ? 'Cursos Técnicos' :
                          /aprendiz senai/i.test(text) ? 'Aprendiz SENAI' :
                          /gradua[cç][aã]o/i.test(text) ? 'Graduação' :
                          /p[oó]s-gradua[cç][aã]o/i.test(text) ? 'Pós-graduação' : null;

            const area = /tecnologia da informa[cç][aã]o e inform[aá]tica/i.test(text)
              ? 'Tecnologia da Informação e Informática'
              : null;

            results.push({
              nome,
              descricao,
              detalhe_url: saibaMais ? saibaMais.href : null,
              inscricao_url: inscreva ? inscreva.href : null,
              carga_horaria,
              unidade: 'SENAI Santana de Parnaíba',
              modalidade,
              nivel,
              area
            });
          }

          return results;
        }
        """
    )

    courses = []
    seen_local = set()

    for item in raw_items:
        course = Course(
            nome=normalize_spaces(item.get("nome", "")),
            descricao=normalize_spaces(item.get("descricao", "")),
            detalhe_url=safe_url(BASE_URL, item.get("detalhe_url")),
            inscricao_url=safe_url(BASE_URL, item.get("inscricao_url")),
            carga_horaria=normalize_spaces(item.get("carga_horaria") or ""),
            unidade=normalize_spaces(item.get("unidade") or ""),
            modalidade=normalize_spaces(item.get("modalidade") or ""),
            nivel=normalize_spaces(item.get("nivel") or ""),
            area=normalize_spaces(item.get("area") or ""),
            modal_id=extract_modal_id(item.get("detalhe_url")),
        )

        # filtro mínimo para evitar títulos que não são curso
        if not course.nome:
            continue
        if len(course.nome) < 4:
            continue

        key = unique_key(course)
        if key in seen_local:
            continue
        seen_local.add(key)
        courses.append(course)

    return courses


def enrich_from_detail_page(browser, course: Course) -> Course:
    """
    Entra na página de detalhe do curso e tenta obter:
    - descrição mais completa
    - link de inscrição, se não veio da listagem

    Se detalhe_url for javascript:, ignora.
    """
    if not course.detalhe_url:
        return course

    # ignora pseudo-links do tipo javascript:openModalInfo(...)
    if course.detalhe_url.strip().lower().startswith("javascript:"):
        return course

    page = browser.new_page()
    try:
        page.goto(course.detalhe_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)

        data = page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();

              let descricao = '';

              const descCandidates = Array.from(document.querySelectorAll('main p, article p, section p'))
                .map(el => norm(el.innerText))
                .filter(Boolean)
                .filter(t => t.length > 80);

              if (descCandidates.length) {
                descricao = descCandidates[0];
              }

              const links = Array.from(document.querySelectorAll('a[href]'));
              const inscreva = links.find(a => /inscreva-se|matricule-se|quero me inscrever/i.test(norm(a.innerText)));

              return {
                descricao,
                inscricao_url: inscreva ? inscreva.href : null
              };
            }
            """
        )

        if data.get("descricao") and len(data["descricao"]) > len(course.descricao or ""):
            course.descricao = normalize_spaces(data["descricao"])

        if not course.inscricao_url and data.get("inscricao_url"):
            course.inscricao_url = safe_url(BASE_URL, data["inscricao_url"])

    except Exception as e:
        print(f"[WARN] Falha ao enriquecer '{course.nome}': {e}")

    finally:
        page.close()

    return course


def go_to_next_page(page) -> bool:
    """
    Tenta avançar a paginação.
    Retorna True se conseguiu, False se não há próxima página.
    """
    # tenta por texto
    next_selectors = [
        "text=Próximo",
        "a:has-text('Próximo')",
        "button:has-text('Próximo')",
        "[aria-label*='Próximo']",
        "[rel='next']",
    ]

    for sel in next_selectors:
        try:
            locator = page.locator(sel).first
            if locator.count() and locator.is_visible():
                locator.click(timeout=3000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                return True
        except Exception:
            continue

    return False


def save_json(courses: List[Course], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in courses], f, ensure_ascii=False, indent=2)


def save_csv(courses: List[Course], path: str) -> None:
    if not courses:
        return

    fields = list(asdict(courses[0]).keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for course in courses:
            writer.writerow(asdict(course))


def main() -> None:
    all_courses: List[Course] = []
    global_seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)

        # percorre páginas
        max_pages = 10
        for _ in range(max_pages):
            page_courses = try_extract_course_cards(page)

            for course in page_courses:
                key = unique_key(course)
                if key in global_seen:
                    continue
                global_seen.add(key)
                all_courses.append(course)

            if not go_to_next_page(page):
                break

        # enriquecer com detalhe
        enriched = []
        for idx, course in enumerate(all_courses, start=1):
            print(f"[{idx}/{len(all_courses)}] Processando: {course.nome}")
            enriched.append(enrich_from_detail_page(browser, course))
            time.sleep(0.5)

        browser.close()

    save_json(enriched, OUTPUT_JSON)
    save_csv(enriched, OUTPUT_CSV)

    print(f"Total de cursos extraídos: {len(enriched)}")
    print(f"Arquivos gerados: {OUTPUT_JSON}, {OUTPUT_CSV}")


if __name__ == "__main__":
    main()