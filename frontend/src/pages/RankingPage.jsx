import { useEffect, useMemo, useState } from 'react'
import {
  HiOutlineTrophy,
  HiOutlineFire,
  HiOutlineSparkles,
  HiOutlineUserCircle
} from 'react-icons/hi2'

import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'
import rankingMock from '../data/rankingMock.json'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export default function RankingPage() {
  const [ranking, setRanking] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadRanking() {
      try {
        setLoading(true)
        setError('')

        // const response = await fetch(`${API_URL}/api/ranking`)

        // if (!response.ok) {
        //   throw new Error('Não foi possível carregar o ranking')
        // }

        // const data = await response.json()
        // setRanking(data.ranking || [])
        setRanking(rankingMock)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadRanking()
  }, [])

  const top3 = useMemo(() => ranking.slice(0, 3), [ranking])

  const totalCertificates = useMemo(() => {
    return ranking.reduce(
      (total, student) => total + Number(student.valid_certificates || 0),
      0
    )
  }, [ranking])

  const leaderName = ranking[0]?.student_name || '--'

  function formatDate(dateValue) {
    if (!dateValue) return 'Sem data'

    return new Date(dateValue).toLocaleDateString('pt-BR')
  }

  function formatConfidence(value) {
    return `${Number(value || 0).toFixed(1)}%`
  }

  return (
    <section className="page-spacing">
      <SectionTitle
        badge="Ranking"
        title="Ranking de certificados"
        subtitle="Acompanhe os alunos com mais certificados válidos na plataforma."
      />

      <div className="stats-grid compact-grid fade-in-up">
        <StatCard
          icon={<HiOutlineTrophy />}
          label="Líder atual"
          value={leaderName}
        />

        <StatCard
          icon={<HiOutlineFire />}
          label="Certificados válidos"
          value={totalCertificates}
        />

        <StatCard
          icon={<HiOutlineSparkles />}
          label="Critério"
          value="Certificados"
        />
      </div>

      {loading && (
        <div className="empty-state">
          Carregando ranking...
        </div>
      )}

      {error && (
        <p className="error">{error}</p>
      )}

      {!loading && !error && !ranking.length && (
        <div className="empty-state">
          Ainda não há certificados válidos para o ranking.
        </div>
      )}

      {!loading && !error && !!ranking.length && (
        <>
          <div className="ranking-podium fade-in-up">
            {[top3[1], top3[0], top3[2]]
              .filter(Boolean)
              .map((student) => {
                const medal =
                  student.position === 1
                    ? '🥇'
                    : student.position === 2
                      ? '🥈'
                      : '🥉'

                return (
                  <article
                    key={`${student.student_cpf}-${student.position}`}
                    className={`ranking-podium-card podium-${student.position}`}
                  >
                    <div className="podium-medal">
                      {medal}
                    </div>

                    <span className="ranking-position">
                      #{student.position}
                    </span>

                    <HiOutlineUserCircle className="ranking-avatar" />

                    <h3>{student.student_name}</h3>

                    <p>
                      {student.valid_certificates} certificados válidos
                    </p>
                  </article>
                )
              })}
          </div>

          <div className="ranking-list-card fade-in-up">
            <h3>Classificação geral</h3>

            <div className="ranking-list">
              {ranking.map((student) => (
                <div
                  key={`${student.student_cpf}-${student.position}`}
                  className="ranking-row"
                >
                  <div className="ranking-row-left">
                    <span className="ranking-row-position">
                      #{student.position}
                    </span>

                    <div>
                      <strong>{student.student_name}</strong>
                    </div>
                  </div>

                  <div className="ranking-row-right">
                    <strong>
                      {student.valid_certificates} certificados
                    </strong>

                    <small>
                      Último envio: {formatDate(student.last_submission)}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  )
}