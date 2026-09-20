import { FormEvent, useState } from 'react'
import { useAuth } from '../AuthContext'

export function AuthPage() {
  const { login, register } = useAuth()
  const [registration, setRegistration] = useState(false)
  const [researcherId, setResearcherId] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const cleanResearcherId = researcherId.trim()
    if (!/^[A-Za-z0-9_.-]{3,50}$/.test(cleanResearcherId)) {
      setMessage('Името трябва да е 3–50 знака: букви, цифри, точка, тире или долна черта.')
      return
    }
    if (password.length < 8 || password.length > 128) {
      setMessage('Паролата трябва да е между 8 и 128 знака.')
      return
    }
    setMessage('')
    setSubmitting(true)
    try {
      if (registration) await register(cleanResearcherId, password)
      else await login(cleanResearcherId, password)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Автентикацията е неуспешна.')
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="auth-page">
    <form className="auth-form" onSubmit={submit} noValidate>
      <p className="eyebrow">ИЗСЛЕДОВАТЕЛСКИ ПОРТАЛ</p>
      <h1>{registration ? 'Регистрация' : 'Вход'}</h1>
      <label>Researcher ID
        <input autoComplete="username" value={researcherId} onChange={event => setResearcherId(event.target.value)} />
      </label>
      <label>Парола
        <input type="password" autoComplete={registration ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} />
      </label>
      {message && <p className="auth-message" role="alert">{message}</p>}
      <button className="auth-submit" type="submit" disabled={submitting}>
        {submitting ? 'Моля, изчакайте…' : registration ? 'Регистрация' : 'Вход'}
      </button>
      <button className="auth-switch" type="button" onClick={() => { setRegistration(value => !value); setMessage('') }}>
        {registration ? 'Към вход' : 'Към регистрация'}
      </button>
    </form>
  </main>
}
