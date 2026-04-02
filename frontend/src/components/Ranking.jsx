export default function Ranking({ ranking }) {
  return (
    <section className="card">
      <div className="section-header">
        <h2>Ranking dos alunos</h2>
        <span>Top participantes</span>
      </div>

      <div className="ranking-list">
        {ranking.map(item => (
          <article key={item.student} className="ranking-item">
            <div className="position">#{item.position}</div>
            <div>
              <strong>{item.student}</strong>
              <p>{item.certificates} certificado(s)</p>
            </div>
            <div className="points">{item.points} pt</div>
          </article>
        ))}
      </div>
    </section>
  )
}
