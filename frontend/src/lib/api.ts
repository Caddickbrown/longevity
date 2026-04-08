import type { BiomarkerReading, Intervention, ProtocolEntry, CorrelationResult, ResearchDigest, JournalEntry, BeliefSnapshot, TeachingListItem, ProtocolExplanation, ConversationMessage } from '@/types'

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

export async function upsertJournalEntry(data: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>): Promise<JournalEntry> {
  const res = await fetch(`${BASE}/journal/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to save journal entry')
  return res.json()
}

export async function getJournalEntries(params?: { from_date?: string; to_date?: string }): Promise<JournalEntry[]> {
  const query = new URLSearchParams()
  if (params?.from_date) query.set('from_date', params.from_date)
  if (params?.to_date) query.set('to_date', params.to_date)
  const qs = query.toString()
  const res = await fetch(`${BASE}/journal/${qs ? `?${qs}` : ''}`)
  if (!res.ok) throw new Error('Failed to fetch journal entries')
  return res.json()
}

export async function getJournalEntry(date: string): Promise<JournalEntry> {
  const res = await fetch(`${BASE}/journal/${date}`)
  if (!res.ok) throw new Error('Failed to fetch journal entry')
  return res.json()
}

export async function createBeliefSnapshot(data: Omit<BeliefSnapshot, 'id' | 'created_at'>): Promise<BeliefSnapshot> {
  const res = await fetch(`${BASE}/beliefs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to create belief snapshot')
  return res.json()
}

export async function getBeliefSnapshots(): Promise<BeliefSnapshot[]> {
  const res = await fetch(`${BASE}/beliefs/`)
  if (!res.ok) throw new Error('Failed to fetch belief snapshots')
  return res.json()
}

export async function getBeliefsByTitle(title: string): Promise<BeliefSnapshot[]> {
  const res = await fetch(`${BASE}/beliefs/by-title/${encodeURIComponent(title)}`)
  if (!res.ok) throw new Error('Failed to fetch beliefs by title')
  return res.json()
}

export async function getTeachingList(): Promise<TeachingListItem[]> {
  const res = await fetch(`${BASE}/teaching/`)
  if (!res.ok) throw new Error('Failed to fetch teaching list')
  return res.json()
}

export async function getTeachingExplanation(interventionId: number): Promise<ProtocolExplanation> {
  const res = await fetch(`${BASE}/teaching/${interventionId}`)
  if (!res.ok) throw new Error('Failed to fetch teaching explanation')
  return res.json()
}

export async function generateExplanation(interventionId: number): Promise<ProtocolExplanation> {
  const res = await fetch(`${BASE}/teaching/generate/${interventionId}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to generate explanation')
  return res.json()
}

export async function generateAllExplanations(): Promise<{ generated: number; skipped: number }> {
  const res = await fetch(`${BASE}/teaching/generate-all`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to generate all explanations')
  return res.json()
}

export async function sendChatMessage(message: string): Promise<ConversationMessage> {
  const res = await fetch(`${BASE}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try { detail = JSON.parse(text)?.detail ?? text } catch { /* use raw text */ }
    throw Object.assign(new Error(detail), { status: res.status })
  }
  return res.json()
}

export async function getChatHistory(): Promise<ConversationMessage[]> {
  const res = await fetch(`${BASE}/chat/history`)
  if (!res.ok) throw new Error('Failed to fetch chat history')
  return res.json()
}

export async function clearChatHistory(): Promise<void> {
  const res = await fetch(`${BASE}/chat/history`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to clear chat history')
}
