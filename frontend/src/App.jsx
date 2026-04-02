import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import CoursesPage from './pages/CoursesPage'
import SubmitCertificatePage from './pages/SubmitCertificatePage'
import RankingPage from './pages/RankingPage'

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />

      <main className="container">
        <Routes>
          <Route path="/" element={<CoursesPage />} />
          <Route path="/submissoes" element={<SubmitCertificatePage />} />
          <Route path="/ranking" element={<RankingPage />} />
        </Routes>
      </main>

      <Footer />
    </div>
  )
}