import type { BiomarkerReading, Intervention, ProtocolEntry, CorrelationResult, ResearchDigest } from '@/types'

const BASE = ''

export async function getBiomarkers(params: {
  metric?: string
  from_date?: string
  to_date?: string
}): Promise<BiomarkerReading[]> {
  const query = new URLSearchParams()
  if (params.metric) query.set('metric', params.metric)
  if (params.from_date) query.set('from_date', params.from_date)
  if (params.to_date) query.set('to_date', params.to_date)
  const res = await fetch(`${BASE}/biomarkers/?${query}`)
  if (!res.ok) throw new Error('Failed to fetch biomarkers')
  return res.json()
}

export async function createBiomarker(data: Omit<BiomarkerReading, 'id' | 'created_at'>): Promise<BiomarkerReading> {
  const res = await fetch(`${BASE}/biomarkers/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to create reading')
  return res.json()
}

export async function getProtocols(tier?: number): Promise<Intervention[]> {
  const query = tier !== undefined ? `?tier=${tier}` : ''
  const res = await fetch(`${BASE}/protocols/${query}`)
  if (!res.ok) throw new Error('Failed to fetch protocols')
  return res.json()
}

export async function getChecklist(date: string): Promise<ProtocolEntry[]> {
  const res = await fetch(`${BASE}/checklist/?date=${date}`)
  if (!res.ok) throw new Error('Failed to fetch checklist')
  return res.json()
}

export async function upsertChecklistEntry(data: {
  intervention_id: number
  date: string
  complied: boolean
  notes?: string
}): Promise<ProtocolEntry> {
  const res = await fetch(`${BASE}/checklist/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes: '', ...data }),
  })
  if (!res.ok) throw new Error('Failed to save checklist entry')
  return res.json()
}

export async function getCorrelation(params: {
  metric: string
  from_date?: string
  to_date?: string
}): Promise<CorrelationResult> {
  const query = new URLSearchParams()
  query.set('metric', params.metric)
  if (params.from_date) query.set('from_date', params.from_date)
  if (params.to_date) query.set('to_date', params.to_date)
  const res = await fetch(`${BASE}/correlation/?${query}`)
  if (!res.ok) throw new Error('Failed to fetch correlation')
  return res.json()
}

export async function getResearchDigests(): Promise<ResearchDigest[]> {
  const res = await fetch(`${BASE}/research/`)
  if (!res.ok) throw new Error('Failed to fetch research digests')
  return res.json()
}

export async function generateResearchDigest(): Promise<ResearchDigest> {
  const res = await fetch(`${BASE}/research/generate`, { method: 'POST' })
  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try { detail = JSON.parse(text)?.detail ?? text } catch { /* use raw text */ }
    throw new Error(detail)
  }
  return res.json()
}

export async function importBloodPanel(file: File): Promise<{ inserted: number; skipped: number }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/blood-panel/import`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try { detail = JSON.parse(text)?.detail ?? text } catch { /* use raw text */ }
    throw new Error(detail)
  }
  return res.json()
}

export async function triggerBackfill(days: number): Promise<{ inserted: number; days_synced: number }> {
  const res = await fetch(`${BASE}/biomarkers/sync/backfill`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ days }),
  })
  if (!res.ok) throw new Error('Backfill failed')
  return res.json()
}
