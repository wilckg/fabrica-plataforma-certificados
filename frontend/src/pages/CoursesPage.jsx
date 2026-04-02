import { useEffect, useMemo, useState } from 'react'
import { HiOutlineAcademicCap, HiOutlineBolt, HiOutlineUsers } from 'react-icons/hi2'
import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'
import CourseCard from '../components/CourseCard'

export default function CoursesPage() {
  const [courses, setCourses] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadCourses() {
      try {
        setLoading(true)
        setError('')

        const response = await fetch('https://organic-parakeet-w9x5p594gr4hgwv5-5000.app.github.dev/api/senai-courses')
        if (!response.ok) throw new Error('Não foi possível carregar os cursos')

        const data = await response.json()
        setCourses(data.courses || data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadCourses()
  }, [])

  const filteredCourses = useMemo(() => {
    return courses.filter((course) =>
      (course.title || '').toLowerCase().includes(search.toLowerCase())
    )
  }, [courses, search])

  return (
    <section className="page-spacing">
      <div className="hero hero-home fade-in-up">
        <div className="hero-content">
          <span className="hero-badge">Cursos gratuitos • Certificados • Ranking</span>
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
            <span className="hero-mini-label">Desafio em andamento</span>
            <strong>Conclua cursos e avance no ranking</strong>
            <p>
              Quanto mais certificados aprovados, maior sua posição na plataforma.
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
          label="Foco em tecnologia"
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

      {loading && <div className="empty-state">Carregando cursos...</div>}
      {error && <p className="error">{error}</p>}

      {!loading && !filteredCourses.length ? (
        <div className="empty-state">
          Nenhum curso encontrado com esse filtro.
        </div>
      ) : (
        <div className="grid">
          {filteredCourses.map((course, index) => (
            <CourseCard key={`${course.title}-${index}`} course={course} />
          ))}
        </div>
      )}
    </section>
  )
}