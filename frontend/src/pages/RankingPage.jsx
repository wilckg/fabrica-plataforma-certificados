import { useEffect, useMemo, useState } from 'react'
import {
  HiOutlineTrophy,
  HiOutlineFire,
  HiOutlineSparkles,
  HiOutlineUserCircle
} from 'react-icons/hi2'
import { LuCrown } from 'react-icons/lu'

import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'

const API_URL =
  import.meta.env.VITE_API_URL ||
  'https://fabrica-plataforma-certificados-backend.onrender.com'

export default function RankingPage() {
  const [ranking, setRanking] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState(null)

  useEffect(() => {
    async function loadRanking() {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${API_URL}/api/ranking?page=${page}&limit=10`)

        if (!response.ok) {
          throw new Error('Não foi possível carregar o ranking')
        }

        const data = await response.json()

        setRanking(data.ranking || [])
        setPagination(data.pagination || null)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadRanking()
  }, [page])

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

  return (
    <section className="page-spacing">
      <SectionTitle
        badge="Ranking"
        title="Ranking de certificados"
        subtitle="Acompanhe os alunos com mais certificados válidos na plataforma."
      />

      <div className="stats-grid compact-grid fade-in-up">
        <StatCard icon={<HiOutlineTrophy />} label="Líder atual" value={leaderName} />
        <StatCard icon={<HiOutlineFire />} label="Certificados válidos" value={totalCertificates} />
        <StatCard icon={<HiOutlineSparkles />} label="Critério" value="Certificados" />
      </div>

      {loading && <div className="empty-state">Carregando ranking...</div>}

      {error && <p className="error">{error}</p>}

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
                    key={`${student.student_cpf_masked}-${student.position}`}
                    className={`ranking-podium-card podium-${student.position}`}
                  >
                    <div className="podium-medal">{medal}</div>

                    {student.position === 1 && (
                      <div className="leader-crown">
                        <LuCrown />
                      </div>
                    )}

                    <span className="ranking-position">#{student.position}</span>

                    <HiOutlineUserCircle className="ranking-avatar" />

                    <div className="podium-name-wrapper">
                      <h3>{student.student_name}</h3>
                    </div>

                    <span className="podium-cpf">
                      {student.student_cpf_masked}
                    </span>

                    <p>{student.valid_certificates} certificados válidos</p>
                  </article>
                )
              })}
          </div>

          <div className="ranking-list-card fade-in-up">
            <h3>Classificação geral</h3>

            <div className="ranking-list">
              {ranking.map((student) => (
                <div
                  key={`${student.student_cpf_masked}-${student.position}`}
                  className="ranking-row"
                >
                  <div className="ranking-row-left">
                    <span className="ranking-row-position">
                      #{student.position}
                    </span>

                    <div className="ranking-student-info">
                      <div className="ranking-name-wrapper">
                        <strong>{student.student_name}</strong>

                        {student.position === 1 && (
                          <LuCrown className="ranking-leader-crown" />
                        )}
                      </div>

                      <span className="ranking-student-cpf">
                        CPF: {student.student_cpf_masked}
                      </span>
                    </div>
                  </div>

                  <div className="ranking-row-right">
                    <strong>{student.valid_certificates} certificados</strong>

                    <small>
                      Último envio: {formatDate(student.last_submission)}
                    </small>
                  </div>
                </div>
              ))}
            </div>

            {pagination && pagination.total_pages > 1 && (
              <div className="ranking-pagination">
                <button
                  type="button"
                  disabled={page === 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  Anterior
                </button>

                <span>
                  Página {pagination.page} de {pagination.total_pages}
                </span>

                <button
                  type="button"
                  disabled={page === pagination.total_pages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Próxima
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  )
}