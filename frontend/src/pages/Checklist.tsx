import { useState, useEffect, useCallback, useMemo, memo } from 'react'
import { getProtocols, getChecklist, upsertChecklistEntry } from '@/lib/api'
import type { Intervention, ProtocolEntry } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'

function toDateString(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function formatDate(d: Date): string {
  return d.toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

type ComplianceMap = Record<number, boolean>

interface ProtocolRowProps {
  protocol: Intervention
  complied: boolean
  onToggle: (id: number, current: boolean) => void
}

const ProtocolRow = memo(function ProtocolRow({ protocol, complied, onToggle }: ProtocolRowProps) {
  return (
    <div className="flex items-center gap-3 py-2 border-b last:border-b-0">
      <Checkbox
        id={'proto-' + String(protocol.id)}
        checked={complied}
        onCheckedChange={() => onToggle(protocol.id, complied)}
      />
      <label htmlFor={'proto-' + String(protocol.id)} className="flex-1 cursor-pointer text-sm font-medium">
        {protocol.name}
      </label>
      <Badge variant="outline" className="text-xs">{protocol.evidence_grade}</Badge>
    </div>
  )
})

export function Checklist() {
  const [date, setDate] = useState<Date>(() => new Date())
  const [protocols, setProtocols] = useState<Intervention[]>([])
  const [compliance, setCompliance] = useState<ComplianceMap>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getProtocols(1)
      .then(setProtocols)
      .catch(() => setError('Failed to load protocols'))
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    getChecklist(toDateString(date))
      .then((entries: ProtocolEntry[]) => {
        const map: ComplianceMap = {}
        for (const e of entries) map[e.intervention_id] = e.complied
        setCompliance(map)
      })
      .catch(() => setError('Failed to load checklist'))
      .finally(() => setLoading(false))
  }, [date])

  const handleToggle = useCallback((id: number, current: boolean) => {
    setCompliance(prev => ({ ...prev, [id]: !current }))
    upsertChecklistEntry({ intervention_id: id, date: toDateString(date), complied: !current })
      .then((entry: ProtocolEntry) => {
        setCompliance(prev => ({ ...prev, [entry.intervention_id]: entry.complied }))
      })
      .catch(() => {
        setCompliance(prev => ({ ...prev, [id]: current }))
      })
  }, [date])

  const prevDay = useCallback(() => setDate(d => { const n = new Date(d); n.setDate(n.getDate() - 1); return n }), [])
  const nextDay = useCallback(() => setDate(d => { const n = new Date(d); n.setDate(n.getDate() + 1); return n }), [])

  const completed = useMemo(
    () => protocols.filter(p => compliance[p.id]).length,
    [protocols, compliance],
  )

  return (
    <div className="max-w-xl mx-auto p-4 space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <Button variant="outline" size="sm" onClick={prevDay}>‹</Button>
            <CardTitle className="text-base font-semibold">{formatDate(date)}</CardTitle>
            <Button variant="outline" size="sm" onClick={nextDay}>›</Button>
          </div>
          <p className="text-sm text-muted-foreground text-center pt-1">
            {completed} / {protocols.length} completed
          </p>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-sm text-muted-foreground py-4 text-center">Loading...</p>}
          {error && <p className="text-sm text-destructive py-4 text-center">{error}</p>}
          {!loading && !error && protocols.map(p => (
            <ProtocolRow
              key={p.id}
              protocol={p}
              complied={!!compliance[p.id]}
              onToggle={handleToggle}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
