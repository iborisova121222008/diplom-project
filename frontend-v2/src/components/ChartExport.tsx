function trigger(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

function serializedSvg(targetId: string) {
  const svg = document.querySelector(`#${targetId} svg`)
  if (!svg) throw new Error('Графиката не е налична за експорт.')
  const clone = svg.cloneNode(true) as SVGElement
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  return new XMLSerializer().serializeToString(clone)
}

export function ChartExportActions({ targetId, filename }: { targetId: string; filename: string }) {
  const exportSvg = () => trigger(new Blob([serializedSvg(targetId)], { type: 'image/svg+xml;charset=utf-8' }), `${filename}.svg`)
  const exportPng = () => {
    const source = serializedSvg(targetId)
    const svg = document.querySelector(`#${targetId} svg`)!
    const bounds = svg.getBoundingClientRect()
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, bounds.width * 2)
    canvas.height = Math.max(1, bounds.height * 2)
    const context = canvas.getContext('2d')!
    context.scale(2, 2)
    context.fillStyle = '#FFFFFF'
    context.fillRect(0, 0, bounds.width, bounds.height)
    const image = new Image()
    const url = URL.createObjectURL(new Blob([source], { type: 'image/svg+xml;charset=utf-8' }))
    image.onload = () => {
      context.drawImage(image, 0, 0, bounds.width, bounds.height)
      URL.revokeObjectURL(url)
      canvas.toBlob(blob => { if (blob) trigger(blob, `${filename}.png`) }, 'image/png')
    }
    image.src = url
  }
  return <span className="chart-export"><button onClick={exportSvg}>SVG</button><button onClick={exportPng}>PNG</button></span>
}
