export default function CourseCard({ course, onSeeMore }) {
  const title = course.title || 'Curso'

  const description =
    course.description || 'Curso disponível para desenvolvimento profissional.'

  const workload =
    course.workload || 'Carga horária não informada'

  const unit = course.unit || 'SENAI-SP'

  const area = (course.area || '').toLowerCase()

  function getCategoryLabel(titleText) {
    const lower = titleText.toLowerCase()

    if (lower.includes('inteligência') || lower.includes('ia')) return 'IA'
    if (lower.includes('excel')) return 'Produtividade'
    if (lower.includes('segurança')) return 'Cibersegurança'
    if (lower.includes('programação')) return 'Programação'
    if (lower.includes('blockchain')) return 'Inovação'

    return 'Tecnologia'
  }

  function getCardVariant() {
    if (area.includes('soft')) return 'card-softskills'

    return 'card-tech'
  }

  const category = getCategoryLabel(title)

  return (
    <article
      className={`card course-card fade-in-up ${getCardVariant()}`}
    >
      <span className="card-tag">{category}</span>

      <h3>{title}</h3>

      <p>{description}</p>

      <div className="card-meta">
        <span className="meta-pill">{workload}</span>
        <span className="meta-pill">{unit}</span>
      </div>

      <div className="card-actions">
        <button
          type="button"
          onClick={onSeeMore}
          className="card-action-link"
        >
          Saiba mais
        </button>

        {course.enroll_url && (
          <a
            href={course.enroll_url}
            target="_blank"
            rel="noreferrer"
            className="card-action-link"
          >
            Inscreva-se
          </a>
        )}
      </div>
    </article>
  )
}