import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Layout } from './components/Layout'
import { ExperimentPage } from './pages/ExperimentPage'

function LocationProbe() {
  return <output aria-label="Текущ адрес">{useLocation().pathname}</output>
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('опростена навигация', () => {
  it('показва точно две основни дестинации и шест подтаба', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/experiment/input']}><Routes><Route element={<Layout />}><Route path="experiment/:tab" element={<ExperimentPage />} /></Route></Routes><LocationProbe /></MemoryRouter></QueryClientProvider>)
    expect(screen.getByRole('navigation', { name: 'Основна навигация' }).querySelectorAll('a')).toHaveLength(2)
    expect(screen.getByRole('navigation', { name: 'Етапи на експеримента' }).querySelectorAll('a')).toHaveLength(6)
    fireEvent.click(screen.getByRole('link', { name: 'Прогнози' }))
    expect(screen.getByLabelText('Текущ адрес').textContent).toBe('/experiment/predictions')
  })
})
