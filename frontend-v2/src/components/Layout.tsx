import {
  BookOpenCheck, Database, FileBarChart, FlaskConical, Home, Menu,
  Network, SearchCode, X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

const navigation = [
  ['/', 'Начало', Home],
  ['/overview', 'Изследователски преглед', BookOpenCheck],
  ['/workflow', 'Работен процес', Network],
  ['/experiments', 'Експерименти', FlaskConical],
  ['/features', 'Характеристики', SearchCode],
  ['/external-validation', 'Външна валидация', Database],
  ['/reports', 'Отчети', FileBarChart],
] as const

export function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const current = navigation.find(([path]) => path === location.pathname)

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Към основното съдържание</a>
    <header className="mobile-header">
      <NavLink to="/" className="brand-small">Молекулярен отговор</NavLink>
      <button className="icon-button" onClick={() => setOpen(!open)} aria-label="Меню">
        {open ? <X /> : <Menu />}
      </button>
    </header>
    <aside className={open ? 'sidebar open' : 'sidebar'}>
      <NavLink to="/" className="brand" onClick={() => setOpen(false)}>
        <span className="brand-mark"><FlaskConical size={21} /></span>
        <span><small>Дипломно изследване</small>Молекулярен отговор</span>
      </NavLink>
      <nav aria-label="Основна навигация">
        {navigation.map(([path, label, Icon]) => <NavLink
          key={path}
          to={path}
          end={path === '/'}
          onClick={() => setOpen(false)}
          className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
        ><Icon size={17} />{label}</NavLink>)}
      </nav>
      <div className="research-note">
        <span className="status-dot" />
        <div><strong>Само за четене</strong><small>Завършени експерименти</small></div>
      </div>
      <p className="not-clinical">Изследователска система — не е клиничен инструмент.</p>
    </aside>
    <main id="main-content">
      {location.pathname !== '/' && <div className="breadcrumb">
        <NavLink to="/">Начало</NavLink><span>/</span><span>{current?.[1]}</span>
      </div>}
      <Outlet />
    </main>
  </div>
}
