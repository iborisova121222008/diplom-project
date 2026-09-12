import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ChartExportActions } from './ChartExport'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('експорт на графика', () => {
  it('създава SVG и PNG файлове от видимата графика', async () => {
    const downloads: string[] = []
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:test') })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { downloads.push(this.download) })
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({
      scale: vi.fn(), fillRect: vi.fn(), drawImage: vi.fn(), fillStyle: '',
    } as unknown as CanvasRenderingContext2D)
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation(callback => { callback(new Blob(['png'])) })
    class ImmediateImage {
      onload: (() => void) | null = null
      set src(_value: string) { queueMicrotask(() => this.onload?.()) }
    }
    vi.stubGlobal('Image', ImmediateImage)
    render(<><div id="chart"><svg width="100" height="50"><rect width="10" height="10" /></svg></div><ChartExportActions targetId="chart" filename="graph" /></>)
    fireEvent.click(screen.getByRole('button', { name: 'SVG' }))
    fireEvent.click(screen.getByRole('button', { name: 'PNG' }))
    await waitFor(() => expect(downloads).toEqual(['graph.svg', 'graph.png']))
  })
})
