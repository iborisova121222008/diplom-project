import { NavLink, Outlet } from 'react-router-dom'

export function Layout() {
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Към основното съдържание</a>
    <header className="topbar">
      <NavLink to="/" className="brand">Молекулярен отговор</NavLink>
      <nav aria-label="Основна навигация">
        <NavLink to="/" end>Начало</NavLink>
        <NavLink to="/experiment">Експеримент</NavLink>
      </nav>
    </header>
    <main id="main-content"><Outlet /></main>
  </div>
}
