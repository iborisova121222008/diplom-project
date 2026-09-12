import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { AuthProvider } from './AuthContext'
import { clearStoredAuth, storeAuth } from './authStorage'
import { Layout } from './components/Layout'
import { ExperimentPage } from './pages/ExperimentPage'

function LocationProbe() {
  return <output aria-label="Текущ адрес">{useLocation().pathname}</output>
}

function Providers({ children, route = '/' }: { children: React.ReactNode; route?: string }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}><AuthProvider><MemoryRouter initialEntries={[route]}>{children}</MemoryRouter></AuthProvider></QueryClientProvider>
}

afterEach(() => {
  cleanup()
  clearStoredAuth()
  vi.unstubAllGlobals()
})

describe('опростена навигация', () => {
  it('показва точно две основни дестинации и шест подтаба', () => {
    storeAuth({ accessToken: 'test-token', researcher_id: 'researcher' })
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    render(<Providers route="/experiment/input"><Routes><Route element={<Layout />}><Route path="experiment/:tab" element={<ExperimentPage />} /></Route></Routes><LocationProbe /></Providers>)
    expect(screen.getByRole('navigation', { name: 'Основна навигация' }).querySelectorAll('a')).toHaveLength(2)
    expect(screen.getByRole('navigation', { name: 'Етапи на експеримента' }).querySelectorAll('a')).toHaveLength(6)
    fireEvent.click(screen.getByRole('link', { name: 'Прогнози' }))
    expect(screen.getByLabelText('Текущ адрес').textContent).toBe('/experiment/predictions')
  })
})

describe('автентикация', () => {
  it('скрива защитената навигация преди вход', () => {
    render(<Providers><App /></Providers>)
    expect(screen.getByText('ИЗСЛЕДОВАТЕЛСКИ ПОРТАЛ')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Вход' })).toBeTruthy()
    expect(screen.queryByRole('navigation', { name: 'Основна навигация' })).toBeNull()
    expect(screen.getByLabelText('Researcher ID')).toBeTruthy()
    expect(screen.getByLabelText('Парола').getAttribute('type')).toBe('password')
    fireEvent.click(screen.getByRole('button', { name: 'Към регистрация' }))
    expect(screen.getByRole('heading', { name: 'Регистрация' })).toBeTruthy()
    expect(screen.getByLabelText('Researcher ID')).toBeTruthy()
  })

  it('влиза, показва потребителя и излиза към защитения екран', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toContain('/api/auth/login')
      return {
        ok: true,
        json: async () => ({
          access_token: 'signed-test-token', token_type: 'bearer', researcher_id: 'researcher',
        }),
      } as Response
    }))
    render(<Providers><App /></Providers>)
    fireEvent.change(screen.getByLabelText('Researcher ID'), { target: { value: 'researcher' } })
    fireEvent.change(screen.getByLabelText('Парола'), { target: { value: 'secure-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Вход' }))

    await screen.findByRole('navigation', { name: 'Основна навигация' })
    expect(screen.getByText('researcher')).toBeTruthy()
    expect(JSON.parse(window.localStorage.getItem('research-dashboard-auth') ?? '{}').accessToken).toBe('signed-test-token')

    fireEvent.click(screen.getByRole('button', { name: 'Изход' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Вход' })).toBeTruthy())
    expect(window.localStorage.getItem('research-dashboard-auth')).toBeNull()
  })

  it('регистрира и удостоверява автоматично с една заявка', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toContain('/api/auth/register')
      expect(init?.method).toBe('POST')
      expect(JSON.parse(String(init?.body))).toEqual({
        researcher_id: 'new.researcher',
        password: 'Secure-Test1!',
      })
      return {
        ok: true,
        json: async () => ({
          access_token: 'registration-token', token_type: 'bearer', researcher_id: 'new.researcher',
        }),
      } as Response
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<Providers><App /></Providers>)

    fireEvent.click(screen.getByRole('button', { name: 'Към регистрация' }))
    fireEvent.change(screen.getByLabelText('Researcher ID'), { target: { value: ' New.Researcher ' } })
    fireEvent.change(screen.getByLabelText('Парола'), { target: { value: 'Secure-Test1!' } })
    fireEvent.click(screen.getByRole('button', { name: 'Регистрация' }))

    await screen.findByRole('navigation', { name: 'Основна навигация' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(screen.getByText('new.researcher')).toBeTruthy()
    expect(JSON.parse(window.localStorage.getItem('research-dashboard-auth') ?? '{}')).toEqual({
      accessToken: 'registration-token',
      researcher_id: 'new.researcher',
    })
  })

  it('заменя суровата мрежова грешка с кратко съобщение', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new TypeError('NetworkError when attempting to fetch resource.')
    }))
    render(<Providers><App /></Providers>)
    fireEvent.change(screen.getByLabelText('Researcher ID'), { target: { value: 'researcher' } })
    fireEvent.change(screen.getByLabelText('Парола'), { target: { value: 'secure-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Вход' }))
    expect((await screen.findByRole('alert')).textContent).toBe('Връзката със сървъра е неуспешна.')
  })
})
