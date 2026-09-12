import { FormEvent, useState } from 'react'
import { useAuth } from '../AuthContext'

const PASSWORD_MESSAGE = 'Паролата трябва да съдържа поне 8 символа, малка и главна буква, цифра и специален символ.'
const RESEARCHER_ID_MESSAGE = 'Researcher ID трябва да е 3–50 знака, да започва с буква или цифра и да съдържа само букви, цифри, ., _ и -.'
const SPECIAL_CHARACTERS = new Set(`!@#$%^&*()_+-=[]{};':"\\|,.<>/?`)

export function AuthPage() {
  const { login, register } = useAuth()
  const [registration, setRegistration] = useState(false)
  const [researcherId, setResearcherId] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const cleanResearcherId = researcherId.trim().toLowerCase()
    if (!/^[\p{L}\p{N}][\p{L}\p{N}._-]{2,49}$/u.test(cleanResearcherId)) {
      setMessage(RESEARCHER_ID_MESSAGE)
      return
    }
    const validPassword = password.length >= 8
      && password.length <= 128
      && password === password.trim()
      && /\p{Ll}/u.test(password)
      && /\p{Lu}/u.test(password)
      && /\p{N}/u.test(password)
      && [...password].some(character => SPECIAL_CHARACTERS.has(character))
    if (registration && !validPassword) {
      setMessage(PASSWORD_MESSAGE)
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
      {registration && <small className="password-rule">{PASSWORD_MESSAGE}</small>}
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
