import { useState } from 'react'

const initialForm = {
  student: '',
  courseTitle: '',
  fileName: ''
}

export default function CertificateForm({ onSubmit }) {
  const [form, setForm] = useState(initialForm)

  function handleChange(event) {
    const { name, value } = event.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0]
    setForm(prev => ({ ...prev, fileName: file ? file.name : '' }))
  }

  function handleSubmit(event) {
    event.preventDefault()

    if (!form.student || !form.courseTitle) return

    onSubmit(form)
    setForm(initialForm)
    event.target.reset()
  }

  return (
    <section className="card">
      <h2>Enviar certificado</h2>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Nome do aluno
          <input name="student" value={form.student} onChange={handleChange} placeholder="Digite o nome" />
        </label>

        <label>
          Curso concluído
          <input name="courseTitle" value={form.courseTitle} onChange={handleChange} placeholder="Nome do curso" />
        </label>

        <label>
          Arquivo do certificado
          <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={handleFileChange} />
        </label>

        {form.fileName && <small>Arquivo selecionado: {form.fileName}</small>}

        <button type="submit">Registrar envio</button>
      </form>
    </section>
  )
}
