import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { ExplorationProvider, useExploration } from './ExplorationContext'

function Probe() {
  const { state, update, reset } = useExploration()
  const location = useLocation()
  return <><output>{state.fold}|{state.model}|{state.probe}</output><output>{location.search}</output>
    <button onClick={() => update({ fold: 7, probe: '204012_s_at', minimumFrequency: 4 })}>Избери fold</button>
    <button onClick={reset}>Нулирай</button></>
}

afterEach(cleanup)

describe('ExplorationContext', () => {
  it('reads bookmarkable selections and updates only explorer query state', () => {
    render(<MemoryRouter initialEntries={['/process/lasso?fold=3&model=sklearn_random_forest']}><ExplorationProvider><Probe /></ExplorationProvider></MemoryRouter>)
    expect(screen.getByText('3|sklearn_random_forest|')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Избери fold' }))
    expect(screen.getByText('7|sklearn_random_forest|204012_s_at')).toBeTruthy()
    expect(screen.getByText(/fold=7/)).toBeTruthy()
    expect(screen.getByText(/frequency=4/)).toBeTruthy()
  })

  it('returns the current explorer to verified defaults', () => {
    render(<MemoryRouter initialEntries={['/process/forest?tree=12&fold=4']}><ExplorationProvider><Probe /></ExplorationProvider></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: 'Нулирай' }))
    expect(screen.getByText('1|custom_random_forest|')).toBeTruthy()
  })
})
