import { NavLink } from 'react-router-dom'
import { HiOutlineAcademicCap, HiOutlineTrophy, HiOutlineDocumentArrowUp } from 'react-icons/hi2'

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-badge">FP</div>

        <div>
          <div className="navbar-title">Plataforma de Certificados</div>
          <div className="navbar-subtitle">SENAI • Fábrica de Programadores</div>
        </div>
      </div>

      <nav className="navbar-links">
        <NavLink to="/" className={({ isActive }) => (isActive ? 'active' : '')}>
          <HiOutlineAcademicCap />
          <span>Cursos</span>
        </NavLink>

        <NavLink to="/submissoes" className={({ isActive }) => (isActive ? 'active' : '')}>
          <HiOutlineDocumentArrowUp />
          <span>Certificados</span>
        </NavLink>

        <NavLink to="/ranking" className={({ isActive }) => (isActive ? 'active' : '')}>
          <HiOutlineTrophy />
          <span>Ranking</span>
        </NavLink>
      </nav>
    </header>
  )
}