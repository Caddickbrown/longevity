import { useEffect, useState } from 'react'
import type { TeachingListItem, ProtocolExplanation } from '@/types'
import { getTeachingList, getTeachingExplanation, generateExplanation, generateAllExplanations } from '@/lib/api'

const TIER_LABELS: Record<number, string> = { 1: 'Tier 1', 2: 'Tier 2', 3: 'Tier 3' }

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'bg-green-100 text-green-800',
  moderate: 'bg-yellow-100 text-yellow-800',
  hard: 'bg-red-100 text-red-800',
}

const GRADE_COLORS: Record<string, string> = {
  A: 'bg-blue-100 text-blue-800',
  B: 'bg-indigo-100 text-indigo-800',
  C: 'bg-purple-100 text-purple-800',
  D: 'bg-gray-100 text-gray-700',
}

function Badge({ label, colorClass }: { label: string; colorClass: string }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${colorClass}`}>
      {label}
    </span>
  )
}

interface CardState {
  expanded: boolean
  generating: boolean
  detail: ProtocolExplanation | null
}

export function Teaching() {
  const [items, setItems] = useState<TeachingListItem[]>([])
  const [cardState, setCardState] = useState<Record<number, CardState>>({})
  const [generatingAll, setGeneratingAll] = useState(false)
  const [generateAllResult, setGenerateAllResult] = useState<{ generated: number; skipped: number } | null>(null)

  async function loadList() {
    const data = await getTeachingList()
    setItems(data)
    setCardState(prev => {
      const next: Record<number, CardState> = {}
      for (const item of data) {
        next[item.intervention_id] = prev[item.intervention_id] ?? {
          expanded: false,
          generating: false,
          detail: null,
        }
      }
      return next
    })
  }

  useEffect(() => { loadList() }, [])

  async function handleToggle(item: TeachingListItem) {
    const id = item.intervention_id
    const current = cardState[id]
    if (!current) return

    const nowExpanded = !current.expanded

    if (nowExpanded && item.has_explanation && !current.detail) {
      setCardState(prev => ({
        ...prev,
        [id]: { ...prev[id], expanded: true },
      }))
      try {
        const detail = await getTeachingExplanation(id)
        setCardState(prev => ({
          ...prev,
          [id]: { ...prev[id], detail },
        }))
      } catch {
        // leave detail null, user can retry
      }
    } else {
      setCardState(prev => ({
        ...prev,
        [id]: { ...prev[id], expanded: nowExpanded },
      }))
    }
  }

  async function handleGenerate(e: React.MouseEvent, item: TeachingListItem) {
    e.stopPropagation()
    const id = item.intervention_id
    setCardState(prev => ({
      ...prev,
      [id]: { ...prev[id], generating: true, expanded: true },
    }))
    try {
      const detail = await generateExplanation(id)
      setItems(prev =>
        prev.map(i => i.intervention_id === id ? { ...i, has_explanation: true, difficulty: detail.difficulty } : i)
      )
      setCardState(prev => ({
        ...prev,
        [id]: { ...prev[id], generating: false, detail },
      }))
    } catch {
      setCardState(prev => ({
        ...prev,
        [id]: { ...prev[id], generating: false },
      }))
    }
  }

  async function handleGenerateAll() {
    setGeneratingAll(true)
    setGenerateAllResult(null)
    try {
      const result = await generateAllExplanations()
      setGenerateAllResult(result)
      await loadList()
    } catch {
      // silently fail, list will still refresh
    } finally {
      setGeneratingAll(false)
    }
  }

  const tiers = [1, 2, 3]

  return (
    <div className="max-w-3xl space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Teaching</h2>
        <div className="flex items-center gap-3">
          {generateAllResult && (
            <span className="text-sm text-muted-foreground">
              Generated {generateAllResult.generated}, skipped {generateAllResult.skipped}
            </span>
          )}
          <button
            onClick={handleGenerateAll}
            disabled={generatingAll}
            className="bg-primary text-primary-foreground rounded px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            {generatingAll ? 'Generating…' : 'Generate All'}
          </button>
        </div>
      </div>

      {tiers.map(tier => {
        const tierItems = items.filter(i => i.tier === tier)
        if (tierItems.length === 0) return null
        return (
          <section key={tier} className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              {TIER_LABELS[tier] ?? `Tier ${tier}`}
            </h3>
            <div className="space-y-2">
              {tierItems.map(item => {
                const id = item.intervention_id
                const state = cardState[id]
                const isExpanded = state?.expanded ?? false
                const isGenerating = state?.generating ?? false
                const detail = state?.detail ?? null

                return (
                  <div
                    key={id}
                    className="border rounded-lg overflow-hidden"
                  >
                    {/* Card header — clickable to toggle */}
                    <div
                      className="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer hover:bg-muted/40 select-none"
                      onClick={() => handleToggle(item)}
                    >
                      <div className="flex items-center gap-2 flex-wrap min-w-0">
                        <span className="font-medium text-sm truncate">{item.name}</span>
                        <Badge
                          label={`Tier ${item.tier}`}
                          colorClass="bg-slate-100 text-slate-700"
                        />
                        <Badge
                          label={`Grade ${item.evidence_grade}`}
                          colorClass={GRADE_COLORS[item.evidence_grade] ?? 'bg-gray-100 text-gray-700'}
                        />
                        {item.difficulty && (
                          <Badge
                            label={item.difficulty}
                            colorClass={DIFFICULTY_COLORS[item.difficulty] ?? 'bg-gray-100 text-gray-700'}
                          />
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {!item.has_explanation && !isGenerating && (
                          <button
                            onClick={(e) => handleGenerate(e, item)}
                            className="bg-secondary text-secondary-foreground rounded px-3 py-1 text-xs font-medium hover:opacity-80"
                          >
                            Generate Explanation
                          </button>
                        )}
                        {isGenerating && (
                          <span className="text-xs text-muted-foreground animate-pulse">Generating…</span>
                        )}
                        <span className="text-xs text-muted-foreground">{isExpanded ? '▲' : '▼'}</span>
                      </div>
                    </div>

                    {/* Expanded content */}
                    {isExpanded && (
                      <div className="border-t px-4 py-4 space-y-4 bg-muted/20">
                        {isGenerating && !detail && (
                          <p className="text-sm text-muted-foreground animate-pulse">Generating explanation…</p>
                        )}
                        {!isGenerating && !detail && item.has_explanation && (
                          <p className="text-sm text-muted-foreground">Loading…</p>
                        )}
                        {!isGenerating && !detail && !item.has_explanation && (
                          <p className="text-sm text-muted-foreground">No explanation generated yet.</p>
                        )}
                        {detail && (
                          <>
                            <section className="space-y-1">
                              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">How it works</h4>
                              <p className="text-sm whitespace-pre-wrap">{detail.explanation}</p>
                            </section>
                            <section className="space-y-1">
                              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Why it matters</h4>
                              <p className="text-sm whitespace-pre-wrap">{detail.why_it_matters}</p>
                            </section>
                            <section className="space-y-1">
                              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">How to implement</h4>
                              <p className="text-sm whitespace-pre-wrap">{detail.how_to_implement}</p>
                            </section>
                            {detail.sources.length > 0 && (
                              <section className="space-y-1">
                                <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Sources</h4>
                                <ul className="space-y-1">
                                  {detail.sources.map((s, i) => (
                                    <li key={i}>
                                      <a
                                        href={s.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm text-blue-600 hover:underline"
                                        onClick={e => e.stopPropagation()}
                                      >
                                        {s.title}
                                      </a>
                                    </li>
                                  ))}
                                </ul>
                              </section>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )
      })}

      {items.length === 0 && (
        <p className="text-sm text-muted-foreground">No protocols found.</p>
      )}
    </div>
  )
}
