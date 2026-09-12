import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LoadingState } from './components/Shared'
import { useAuth } from './AuthContext'
import { AuthPage } from './pages/AuthPage'

const HomePage = lazy(() => import('./pages/HomePage').then(module => ({ default: module.HomePage })))
const ExperimentPage = lazy(() => import('./pages/ExperimentPage').then(module => ({ default: module.ExperimentPage })))

export default function App() {
  const { session } = useAuth()
  if (!session) return <AuthPage />

  return <Suspense fallback={<LoadingState label="Зареждане…" />}><Routes>
    <Route element={<Layout />}>
      <Route index element={<HomePage />} />
      <Route path="experiment" element={<ExperimentPage />} />
      <Route path="experiment/:tab" element={<ExperimentPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route>
  </Routes></Suspense>
}
