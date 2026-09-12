import { LogOut } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import geneResponseLogo from '../../GeneResponse-Lab-logo-2b.png'

export function Layout() {
  const { session, logout } = useAuth()
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Към основното съдържание</a>
    <header className="topbar">
      <NavLink to="/" className="brand" aria-label="GeneResponse Lab">
        <img className="brand-logo" src={geneResponseLogo} alt="GeneResponse Lab" />
      </NavLink>
      <div className="topbar-actions">
        <nav aria-label="Основна навигация">
          <NavLink to="/" end>Начало</NavLink>
          <NavLink to="/experiment">Експеримент</NavLink>
        </nav>
        <span className="researcher-session">
          <span>{session?.researcher_id}</span>
          <button
            type="button"
            className="logout-icon-button"
            onClick={logout}
            aria-label="Изход"
            title="Изход"
          >
            <LogOut size={17} strokeWidth={1.8} aria-hidden="true" />
          </button>
        </span>
      </div>
    </header>
    <main id="main-content"><Outlet /></main>
  </div>
}
