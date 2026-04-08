import { useEffect, useState } from 'react'
import { getProtocols } from '@/lib/api'
import type { Intervention } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const TIERS = ['All', 'Tier 1', 'Tier 2', 'Tier 3'] as const
type TierFilter = (typeof TIERS)[number]

function evidenceBadgeVariant(grade: string): string {
  if (grade === 'A') return 'bg-green-100 text-green-800'
  if (grade === 'B') return 'bg-yellow-100 text-yellow-800'
  return 'bg-orange-100 text-orange-800'
}

function costLabel(costTier: number): string {
  return '£'.repeat(Math.max(1, Math.min(3, costTier)))
}

export function Protocols() {
  const [selected, setSelected] = useState<TierFilter>('All')
  const [protocols, setProtocols] = useState<Intervention[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    const tierArg = selected === 'All' ? undefined : (TIERS.indexOf(selected) as 1 | 2 | 3)
    getProtocols(tierArg)
      .then(setProtocols)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Unknown error'))
      .finally(() => setLoading(false))
  }, [selected])

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Protocol Library</h1>

      <div className="flex gap-2 mb-6">
        {TIERS.map((t) => (
          <Button
            key={t}
            variant={selected === t ? 'default' : 'outline'}
            onClick={() => setSelected(t)}
          >
            {t}
          </Button>
        ))}
      </div>

      {loading && <p className="text-muted-foreground">Loading protocols…</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {!loading && !error && protocols.length === 0 && (
        <p className="text-muted-foreground">No protocols found for this tier.</p>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {protocols.map((p) => (
            <Card key={p.id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg leading-snug">{p.name}</CardTitle>
                  <div className="flex gap-1 shrink-0">
                    <span
                      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold ${evidenceBadgeVariant(p.evidence_grade)}`}
                    >
                      {p.evidence_grade}
                    </span>
                    <Badge variant="outline">{costLabel(p.cost_tier)}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm">{p.mechanism}</p>
                {p.references && (
                  <p className="text-xs text-muted-foreground">{p.references}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
