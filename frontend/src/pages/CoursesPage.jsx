import { useMemo, useState } from 'react'
import { HiOutlineAcademicCap, HiOutlineBolt, HiOutlineUsers } from 'react-icons/hi2'
import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'
import CourseCard from '../components/CourseCard'
import rawCourses from '../data/courses.json'

export default function CoursesPage() {
  const [search, setSearch] = useState('')
  const [selectedCourse, setSelectedCourse] = useState(null)

  const courses = useMemo(() => {
    const list = rawCourses.courses || rawCourses

    return list
      .filter((item) => item.nome !== 'Aguarde...')
      .map((item) => ({
        title: item.title || item.nome || 'Curso',
        description:
          item.description ||
          item.descricao ||
          item.area ||
          'Curso disponível no catálogo do SENAI.',
        workload: String(item.workload || item.carga_horaria || '')
          .replace(/SAIBA MAIS/gi, '')
          .trim(),
        enroll_url: item.enroll_url || item.inscricao_url || null,
        source: item.source || 'SENAI-SP',
        unit: item.unit || item.unidade || '',
        modality: item.modality || item.modalidade || '',
        level: item.level || item.nivel || '',
        area: item.area || '',
      }))
  }, [])

  const filteredCourses = useMemo(() => {
    const term = search.toLowerCase().trim()

    return courses.filter((course) =>
      (course.title || '').toLowerCase().includes(term)
    )
  }, [courses, search])

  return (
    <section className="page-spacing">
      <div className="hero hero-home fade-in-up">
        <div className="hero-content">
          <span className="hero-badge">
            Cursos gratuitos • Certificados • Ranking
          </span>

          <h1>Suba de nível com cursos do SENAI</h1>

          <p>
            Explore cursos, envie seus certificados e acompanhe sua evolução em uma
            plataforma moderna, jovem e com identidade institucional.
          </p>

          <div className="hero-actions">
            <a href="#catalogo" className="button">
              Explorar cursos
            </a>

            <a href="/submissoes" className="button-outline">
              Enviar certificado
            </a>
          </div>
        </div>

        <div className="hero-side-card">
          <div className="hero-mini-panel">
            <span className="hero-mini-label">
              Desafio em andamento
            </span>

            <strong>
              Conclua cursos e avance no ranking
            </strong>

            <p>
              Quanto mais certificados aprovados,
              maior sua posição na plataforma.
            </p>
          </div>
        </div>
      </div>

      <div className="stats-grid fade-in-up">
        <StatCard
          icon={<HiOutlineAcademicCap />}
          label="Cursos disponíveis"
          value={courses.length}
        />

        <StatCard
          icon={<HiOutlineBolt />}
          label="Foco em tecnologia e empregabilidade"
          value="100%"
        />

        <StatCard
          icon={<HiOutlineUsers />}
          label="Experiência colaborativa"
          value="Ranking"
        />
      </div>

      <div id="catalogo">
        <SectionTitle
          badge="Catálogo"
          title="Escolha seu próximo curso"
          subtitle="Busque entre os cursos gratuitos disponíveis e encontre opções para avançar em tecnologia."
        />
      </div>

      <div className="toolbar">
        <input
          type="text"
          placeholder="Buscar por nome do curso..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input"
        />
      </div>

      {!filteredCourses.length ? (
        <div className="empty-state">
          Nenhum curso encontrado com esse filtro.
        </div>
      ) : (
        <div className="grid">
          {filteredCourses.map((course, index) => (
            <CourseCard
              key={`${course.title}-${index}`}
              course={course}
              onSeeMore={() => setSelectedCourse(course)}
            />
          ))}
        </div>
      )}

      {selectedCourse && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedCourse(null)}
        >
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modal-close"
              onClick={() => setSelectedCourse(null)}
            >
              ×
            </button>

            <span className="hero-badge">
              {selectedCourse.modality}
            </span>

            <h2>{selectedCourse.title}</h2>

            <div className="modal-description">
              <h4>Sobre o curso</h4>

              <p>
                {selectedCourse.description ||
                  'Descrição não disponível para este curso.'}
              </p>
            </div>

            <div className="modal-info">
              <span>
                <strong>Carga horária:</strong>{' '}
                {selectedCourse.workload}
              </span>

              <span>
                <strong>Unidade:</strong>{' '}
                {selectedCourse.unit}
              </span>

              <span>
                <strong>Nível:</strong>{' '}
                {selectedCourse.level}
              </span>

              <span>
                <strong>Área:</strong>{' '}
                {selectedCourse.area}
              </span>
            </div>

            {selectedCourse.enroll_url && (
              <a
                href={selectedCourse.enroll_url}
                target="_blank"
                rel="noreferrer"
                className="button"
              >
                Fazer inscrição
              </a>
            )}
          </div>
        </div>
      )}
    </section>
  )
}