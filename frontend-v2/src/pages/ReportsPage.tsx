import { useQuery } from '@tanstack/react-query'
import { Download, FileJson, FileSpreadsheet } from 'lucide-react'
import { api } from '../api'
import { EmptyState, ErrorState, LoadingState, PageHeader, SourceNote } from '../components/Shared'

export function ReportsPage() {
  const query = useQuery({ queryKey: ['reports'], queryFn: api.reports })
  if (query.isLoading) return <LoadingState />
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()} />
  return <div className="page">
    <PageHeader eyebrow="Проследимост" title="Отчети и експорти" description="Изтегляне само на съществуващи или проверено генерирани отчети от PostgreSQL. Нито един експорт не променя експерименталните записи." />
    {!query.data?.length ? <EmptyState /> : <section className="report-list">{query.data.map(report => <article className="panel" key={report.key}>
      <span className="report-icon">{report.format === 'JSON' ? <FileJson /> : <FileSpreadsheet />}</span><div><p className="panel-label">{report.format}</p><h2>{report.title}</h2><p>{report.description}</p><SourceNote paths={report.source_paths} /></div><a className="button secondary" href={api.exportUrl(report.download_url)}><Download size={16} /> Изтегли</a>
    </article>)}</section>}
    <section className="panel provenance"><h2>Какво се запазва като произход?</h2><p>Експортите използват записаните dataset IDs, модели, параметри, прагове, метрики и източници. Когато Git commit, изпълнителна среда или време за обучение не са записани, те не се допълват с предположения.</p></section>
  </div>
}
