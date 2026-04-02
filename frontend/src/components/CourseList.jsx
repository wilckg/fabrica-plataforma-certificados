export default function CourseList({ courses }) {
  return (
    <section className="card">
      <div className="section-header">
        <h2>Catálogo de cursos</h2>
        <span>{courses.length} resultado(s)</span>
      </div>

      <div className="course-list">
        {courses.map(course => (
          <article key={course.id} className="course-card">
            <div>
              <p className="course-category">{course.category}</p>
              <h3>{course.title}</h3>
            </div>
            <a href={course.url} target="_blank" rel="noreferrer">
              Acessar curso
            </a>
          </article>
        ))}

        {courses.length === 0 && <p>Nenhum curso encontrado.</p>}
      </div>
    </section>
  )
}
