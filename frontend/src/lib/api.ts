import type { BiomarkerReading, Intervention, ProtocolEntry } from '@/types'

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

export async function triggerBackfill(days: number): Promise<{ inserted: number; days_synced: number }> {
  const res = await fetch(`${BASE}/biomarkers/sync/backfill`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ days }),
  })
  if (!res.ok) throw new Error('Backfill failed')
  return res.json()
}
