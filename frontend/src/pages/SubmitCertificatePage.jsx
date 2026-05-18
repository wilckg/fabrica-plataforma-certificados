import { useMemo, useState } from 'react'
import { HiOutlineCloudArrowUp, HiOutlineDocumentCheck } from 'react-icons/hi2'
import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'
import rawCourses from '../data/courses.json'

export default function SubmitCertificatePage() {
  const [form, setForm] = useState({
    student_name: '',
    student_cpf: '',
    course_title: ''
  })

  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const courses = useMemo(() => {
    const list = rawCourses.courses || rawCourses

    return list
      .filter((item) => item.nome !== 'Aguarde...')
      .map((item) => ({
        title: item.title || item.nome || 'Curso'
      }))
  }, [])

  function formatCPF(value) {
    return value
      .replace(/\D/g, '')
      .slice(0, 11)
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }

  function handleChange(e) {
    const { name, value } = e.target

    setForm({
      ...form,
      [name]: name === 'student_cpf' ? formatCPF(value) : value
    })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setMessage('')
    setError('')

    try {
      const formData = new FormData()
      formData.append('student_name', form.student_name)
      formData.append('student_cpf', form.student_cpf)
      formData.append('course_title', form.course_title)
      formData.append('certificate', file)

      const response = await fetch('http://localhost:5000/api/submissions', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Erro ao enviar certificado')
      }

      setMessage('Certificado enviado com sucesso!')

      setForm({
        student_name: '',
        student_cpf: '',
        course_title: ''
      })

      setFile(null)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page-spacing">
      <SectionTitle
        badge="Submissão"
        title="Envie seu certificado"
        subtitle="Após concluir o curso, envie seu certificado para validação e conte pontos no ranking."
      />

      <div className="stats-grid compact-grid fade-in-up">
        <StatCard
          icon={<HiOutlineCloudArrowUp />}
          label="Formatos aceitos"
          value="PDF/JPG/PNG"
        />

        <StatCard
          icon={<HiOutlineDocumentCheck />}
          label="Validação"
          value="Pendente"
        />
      </div>

      <div className="form-shell fade-in-up">
        <form onSubmit={handleSubmit} className="form-grid">
          <div className="form-row-2">
            <input
              className="input"
              name="student_name"
              placeholder="Seu nome completo"
              value={form.student_name}
              onChange={handleChange}
              required
            />

            <input
              className="input"
              name="student_cpf"
              placeholder="Seu CPF"
              value={form.student_cpf}
              onChange={handleChange}
              inputMode="numeric"
              maxLength="14"
              required
            />
          </div>

          <select
            className="input"
            name="course_title"
            value={form.course_title}
            onChange={handleChange}
            required
          >
            <option value="">Selecione um curso</option>

            {courses.map((course, index) => (
              <option key={`${course.title}-${index}`} value={course.title}>
                {course.title}
              </option>
            ))}
          </select>

          <div className="upload-box custom-upload">
            <input
              id="certificate"
              className="upload-input"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setFile(e.target.files[0])}
              required
            />

            <label htmlFor="certificate" className="upload-label">
              <HiOutlineCloudArrowUp className="upload-icon" />

              <strong>
                {file ? file.name : 'Clique para enviar seu certificado'}
              </strong>

              <span>
                PDF, PNG ou JPG • arquivo legível
              </span>
            </label>
          </div>

          <button className="button" type="submit">
            Enviar certificado
          </button>
        </form>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </div>
    </section>
  )
}