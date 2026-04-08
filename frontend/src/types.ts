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

export interface CorrelationResult {
  metric: string
  from_date: string
  to_date: string
  data: { date: string; value: number; compliance: number }[]
  pearson_r: number | null
  p_value: number | null
}

export interface ResearchDigest {
  id: number
  generated_at: string
  source: string
  summary: string
  interventions_mentioned: string[]
  raw_response: string
}

export interface JournalEntry {
  id: number
  date: string
  body: string
  tags: string[]
  mood: number | null
  energy: number | null
  created_at: string
  updated_at: string
}

export interface BeliefSnapshot {
  id: number
  title: string
  body: string
  tags: string[]
  created_at: string
}

export interface TeachingListItem {
  intervention_id: number
  name: string
  tier: number
  evidence_grade: string
  has_explanation: boolean
  difficulty: string | null
}

export interface ProtocolExplanation {
  id: number
  intervention_id: number
  explanation: string
  why_it_matters: string
  how_to_implement: string
  sources: { title: string; url: string }[]
  difficulty: string
  generated_at: string
}

export interface ConversationMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
