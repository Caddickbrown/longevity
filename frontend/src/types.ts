export interface BiomarkerReading {
  id: number
  source: string
  metric: string
  value: number
  unit: string
  recorded_at: string
  created_at: string
}

export interface Intervention {
  id: number
  name: string
  tier: number
  evidence_grade: string
  cost_tier: number
  mechanism: string
  references: string
  started_at: string | null
  ended_at: string | null
}

export interface ProtocolEntry {
  id: number
  intervention_id: number
  date: string
  complied: boolean
  notes: string
  created_at: string
}
