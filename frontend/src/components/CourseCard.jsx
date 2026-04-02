export default function CourseCard({ course }) {
  const title = course.title || 'Curso'
  const description =
    course.description || 'Curso disponível para desenvolvimento profissional.'
  const workload = course.workload || 'Carga horária não informada'
  const source = course.source || 'SENAI-SP'

  function getCategoryLabel(titleText) {
    const lower = titleText.toLowerCase()

    if (lower.includes('inteligência') || lower.includes('ia')) return 'IA'
    if (lower.includes('excel')) return 'Produtividade'
    if (lower.includes('segurança')) return 'Cibersegurança'
    if (lower.includes('programação')) return 'Programação'
    if (lower.includes('blockchain')) return 'Inovação'
    return 'Tecnologia'
  }

  const category = getCategoryLabel(title)

  return (
    <article className="card course-card fade-in-up">
      <span className="card-tag">{category}</span>

      <h3>{title}</h3>
      <p>{description}</p>

      <div className="card-meta">
        <span className="meta-pill">{workload}</span>
        <span className="meta-pill">{source}</span>
      </div>

      <div className="card-actions">
        <a href={course.details_url} target="_blank" rel="noreferrer">
          Saiba mais
        </a>
        <a href={course.enroll_url} target="_blank" rel="noreferrer">
          Inscreva-se
        </a>
      </div>
    </article>
  )
}