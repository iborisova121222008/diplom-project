import { BarChart3, Boxes, ChevronDown, Dna, FileDown, FlaskConical, Home, Menu, Network, PanelLeftClose, Trees, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../api'
import { useExploration } from '../context/ExplorationContext'

const groups = [
  { label: '', items: [['/', 'Начало', Home]] },
  { label: 'Резултати', items: [
    ['/overview', 'Преглед', BarChart3], ['/experiments', 'Експерименти', FlaskConical],
    ['/external-validation', 'Външна валидация', Boxes], ['/reports', 'Отчети и експорт', FileDown],
  ] },
  { label: 'ML процес', items: [
    ['/process', 'Карта на процеса', Network], ['/process/nested-cv', 'Nested CV', PanelLeftClose],
    ['/process/lasso', 'LASSO и стабилност', Dna], ['/process/forest', 'Random Forest', Trees],
    ['/process/generalization', 'Генерализация', BarChart3],
  ] },
] as const

export function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const { state, update } = useExploration()
  const experiments = useQuery({ queryKey: ['experiments'], queryFn: () => api.experiments() })
  const internal = location.pathname !== '/'

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Към основното съдържание</a>
    <header className="app-header">
      <button className="icon-button mobile-only" onClick={() => setOpen(!open)} aria-label="Навигация">{open ? <X /> : <Menu />}</button>
      <NavLink to="/" className="project-mark"><span>MR</span><strong>Молекулярен отговор</strong></NavLink>
      {internal && <div className="global-context" aria-label="Активен контекст">
        <label><span>Експеримент</span><select value={state.experiment} onChange={event => update({ experiment: event.target.value })}>
          {(experiments.data ?? []).map(item => <option key={item.slug} value={item.slug}>{item.name}</option>)}
        </select><ChevronDown size={13} /></label>
        <label><span>Модел</span><select value={state.model} onChange={event => update({ model: event.target.value })}>
          <option value="custom_random_forest">Custom RF</option><option value="sklearn_random_forest">Sklearn RF</option><option value="lasso_logistic">LASSO</option><option value="l2_logistic">L2 Logistic</option>
        </select><ChevronDown size={13} /></label>
        <code>{state.dataset}</code>
      </div>}
    </header>
    <aside className={open ? 'sidebar open' : 'sidebar'}>
      <nav aria-label="Основна навигация">{groups.map(group => <section key={group.label || 'home'}>
        {group.label && <h2>{group.label}</h2>}
        {group.items.map(([path, label, Icon]) => <NavLink key={path} to={path} end={path === '/' || path === '/process'} onClick={() => setOpen(false)} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}><Icon size={15} />{label}</NavLink>)}
      </section>)}</nav>
    </aside>
    <main id="main-content"><Outlet /></main>
  </div>
}
