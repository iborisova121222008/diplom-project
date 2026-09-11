export interface SourcedFact {
  value: string
  label: string
  year: number
  sourceName: string
  sourceUrl: string
}

const sourceName = 'OECD / Европейска комисия — Профил на България за рака 2025'
const sourceUrl = 'https://www.oecd.org/en/publications/eu-country-cancer-profile-bulgaria-2025_c6533317-en.html'

export const bulgariaCancerFacts: SourcedFact[] = [
  {
    value: '≈25%',
    label: 'от новите онкологични диагнози при жените са рак на гърдата',
    year: 2022,
    sourceName,
    sourceUrl,
  },
  {
    value: '88 на 100 000',
    label: 'възрастово стандартизирана заболяемост при жените',
    year: 2022,
    sourceName,
    sourceUrl,
  },
  {
    value: '36% срещу 66%',
    label: 'мамографско покритие в България спрямо ЕС при жени на 50–69 г.',
    year: 2019,
    sourceName,
    sourceUrl,
  },
]
