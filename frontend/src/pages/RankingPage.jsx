import { useEffect, useMemo, useState } from 'react'
import { HiOutlineTrophy, HiOutlineFire, HiOutlineSparkles } from 'react-icons/hi2'
import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'

export default function RankingPage() {
  const [ranking, setRanking] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadRanking() {
      try {
        const response = await fetch('http://localhost:5000/api/ranking')
        const data = await response.json()
        setRanking(data)
      } catch {
        setRanking([])
      } finally {
        setLoading(false)
      }
    }

    loadRanking()
  }, [])

  const top3 = useMemo(() => ranking.slice(0, 3), [ranking])
  const rest = useMemo(() => ranking.slice(3), [ranking])

  return (
    <section className="page-spacing">
      <SectionTitle
        badge="Ranking"
        title="Quem está em destaque"
        subtitle="Acompanhe os alunos com mais certificados aprovados e veja quem está avançando na plataforma."
      />

      <div className="stats-grid compact-grid fade-in-up">
        <StatCard
          icon={<HiOutlineTrophy />}
          label="Top posição"
          value={ranking.length ? `#1` : '--'}
        />
        <StatCard
          icon={<HiOutlineFire />}
          label="Competição ativa"
          value="Sim"
        />
        <StatCard
          icon={<HiOutlineSparkles />}
          label="Critério"
          value="Certificados"
        />
      </div>

      {loading ? (
        <div className="empty-state">Carregando ranking...</div>
      ) : !ranking.length ? (
        <div className="empty-state">Ainda não há alunos no ranking.</div>
      ) : (
        <div className="ranking-shell">
          <div className="top3 fade-in-up">
            {top3.map((student, index) => (
              <div key={student.id || index} className={`podium-card podium-${index + 1}`}>
                <div className="podium-position">#{index + 1}</div>
                <h3>{student.name}</h3>
                <p>{student.total_certificados} certificados aprovados</p>
              </div>
            ))}
          </div>

          <div className="ranking-list fade-in-up">
            {rest.map((student, index) => (
              <div key={student.id || index} className="ranking-item">
                <span className="ranking-item-position">#{index + 4}</span>
                <span className="ranking-item-name">{student.name}</span>
                <span className="ranking-item-score">
                  {student.total_certificados} certificados
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}