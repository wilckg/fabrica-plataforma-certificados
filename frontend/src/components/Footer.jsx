export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="footer">
      <div className="footer-content">
        <strong>Plataforma de Certificados</strong>

        <p>
          Ambiente de acompanhamento de cursos,
          submissão de certificados e ranking de desempenho.
        </p>

        <div className="footer-divider" />

        <span className="footer-copyright">
          © {year} Wilck Gomes • Todos os direitos reservados.
        </span>
      </div>
    </footer>
  )
}