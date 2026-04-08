import { memo, useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getBiomarkers, triggerBackfill } from '@/lib/api'
import type { BiomarkerReading } from '@/types'

const METRICS = [
  { key: 'steps',            label: 'Steps',         unit: '',    color: '#10b981' },
  { key: 'resting_hr',       label: 'Resting HR',    unit: 'bpm', color: '#f43f5e' },
  { key: 'sleep_total_mins', label: 'Sleep',         unit: 'min', color: '#8b5cf6' },
  { key: 'sleep_deep_mins',  label: 'Deep Sleep',    unit: 'min', color: '#6366f1' },
  { key: 'weight_kg',        label: 'Weight',        unit: 'kg',  color: '#f59e0b' },
  { key: 'body_fat_pct',     label: 'Body Fat',      unit: '%',   color: '#ef4444' },
  { key: 'active_energy_kcal', label: 'Active Cal', unit: 'kcal', color: '#3b82f6' },
  { key: 'distance_km',      label: 'Distance',      unit: 'km',  color: '#14b8a6' },
]

const MetricCard = memo(function MetricCard({
  metricKey, label, unit, color, refreshKey
}: {
  metricKey: string; label: string; unit: string; color: string; refreshKey: number
}) {
  const [data, setData] = useState<BiomarkerReading[]>([])

  useEffect(() => {
    const to = new Date().toISOString().split('T')[0]
    const from = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    getBiomarkers({ metric: metricKey, from_date: from, to_date: to })
      .then(setData)
      .catch(console.error)
  }, [metricKey, refreshKey])

  const chartData = data.map(r => ({
    date: r.recorded_at.split('T')[0],
    value: r.value,
  }))

  const latest = data.at(-1)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        {latest ? (
          <p className="text-2xl font-bold">
            {latest.value % 1 === 0 ? latest.value.toFixed(0) : latest.value.toFixed(1)}
            {unit ? <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span> : null}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">No data</p>
        )}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={80}>
          <LineChart data={chartData}>
            <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
            <XAxis dataKey="date" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(v) => [`${typeof v === 'number' ? v.toFixed(1) : v}${unit}`, label]}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
})

const MANUAL_METRICS = [
  { value: 'blood_pressure_systolic',  label: 'BP Systolic',  unit: 'mmHg' },
  { value: 'blood_pressure_diastolic', label: 'BP Diastolic', unit: 'mmHg' },
  { value: 'mood',                     label: 'Mood',         unit: '/10'  },
  { value: 'energy',                   label: 'Energy',       unit: '/10'  },
  { value: 'symptom_pain',             label: 'Pain Level',   unit: '/10'  },
]

const ManualEntryForm = memo(function ManualEntryForm({ onSaved }: { onSaved: () => void }) {
  const [metric, setMetric] = useState(MANUAL_METRICS[0].value)
  const [value, setValue] = useState('')
  const [saving, setSaving] = useState(false)

  const selectedMetric = MANUAL_METRICS.find(m => m.value === metric)!

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const num = parseFloat(value)
    if (isNaN(num)) return
    setSaving(true)
    try {
      await fetch('/biomarkers/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: 'manual',
          metric,
          value: num,
          unit: selectedMetric.unit,
          recorded_at: new Date().toISOString(),
        }),
      })
      setValue('')
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Log Reading</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex gap-2 items-end flex-wrap">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Metric</label>
            <select
              className="border rounded px-2 py-1 text-sm bg-background"
              value={metric}
              onChange={e => setMetric(e.target.value)}
            >
              {MANUAL_METRICS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground">Value ({selectedMetric.unit})</label>
            <input
              type="number"
              step="0.1"
              className="border rounded px-2 py-1 text-sm w-24 bg-background"
              value={value}
              onChange={e => setValue(e.target.value)}
              required
            />
          </div>
          <Button type="submit" size="sm" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
})

export function Dashboard() {
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  async function handleBackfill() {
    setSyncing(true)
    setSyncResult(null)
    try {
      const result = await triggerBackfill(90)
      setSyncResult(`Synced ${result.days_synced} days — ${result.inserted} new readings`)
      setRefreshKey(k => k + 1)
    } catch {
      setSyncResult('Sync failed — check connection to health-at-home')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Biomarkers — Last 30 Days</h2>
        <div className="flex items-center gap-3">
          {syncResult ? <p className="text-sm text-muted-foreground">{syncResult}</p> : null}
          <Button variant="outline" size="sm" onClick={handleBackfill} disabled={syncing}>
            {syncing ? 'Syncing…' : 'Sync Health Data'}
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {METRICS.map(m => (
          <MetricCard
            key={m.key}
            metricKey={m.key}
            label={m.label}
            unit={m.unit}
            color={m.color}
            refreshKey={refreshKey}
          />
        ))}
      </div>
      <ManualEntryForm onSaved={() => setRefreshKey(k => k + 1)} />
    </div>
  )
}
