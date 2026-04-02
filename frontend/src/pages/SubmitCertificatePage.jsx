import { useEffect, useState } from 'react'
import { HiOutlineCloudArrowUp, HiOutlineDocumentCheck } from 'react-icons/hi2'
import SectionTitle from '../components/SectionTitle'
import StatCard from '../components/StatCard'

export default function SubmitCertificatePage() {
  const [courses, setCourses] = useState([])
  const [form, setForm] = useState({
    student_name: '',
    student_email: '',
    course_title: ''
  })
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadCourses() {
      try {
        const response = await fetch('http://localhost:5000/api/senai-courses')
        const data = await response.json()
        setCourses(data.courses || data)
      } catch {
        setCourses([])
      }
    }

    loadCourses()
  }, [])

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setMessage('')
    setError('')

    try {
      const formData = new FormData()
      formData.append('student_name', form.student_name)
      formData.append('student_email', form.student_email)
      formData.append('course_title', form.course_title)
      formData.append('certificate', file)

      const response = await fetch('http://localhost:5000/api/submissions', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Erro ao enviar certificado')

      setMessage('Certificado enviado com sucesso!')
      setForm({
        student_name: '',
        student_email: '',
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
              name="student_email"
              type="email"
              placeholder="Seu e-mail"
              value={form.student_email}
              onChange={handleChange}
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

          <div className="upload-box">
            <p className="form-help">
              Envie seu certificado em PDF, PNG ou JPG. Certifique-se de que o arquivo
              esteja legível.
            </p>
            <input
              className="input"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setFile(e.target.files[0])}
              required
            />
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