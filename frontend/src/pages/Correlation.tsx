import { useState, useCallback } from 'react'
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getCorrelation } from '@/lib/api'
import type { CorrelationResult } from '@/types'

const METRICS = [
  { key: 'steps',               label: 'Steps' },
  { key: 'resting_hr',          label: 'Resting HR' },
  { key: 'sleep_total_mins',    label: 'Sleep Total (min)' },
  { key: 'sleep_deep_mins',     label: 'Deep Sleep (min)' },
  { key: 'weight_kg',           label: 'Weight (kg)' },
  { key: 'body_fat_pct',        label: 'Body Fat (%)' },
  { key: 'active_energy_kcal',  label: 'Active Calories (kcal)' },
  { key: 'distance_km',         label: 'Distance (km)' },
]

function defaultDates() {
  const to = new Date()
  const from = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)
  return {
    from: from.toISOString().split('T')[0],
    to: to.toISOString().split('T')[0],
  }
}

function interpretR(r: number): string {
  const abs = Math.abs(r)
  const direction = r >= 0 ? 'positive' : 'negative'
  let strength: string
  if (abs >= 0.7) strength = 'strong'
  else if (abs >= 0.4) strength = 'moderate'
  else if (abs >= 0.1) strength = 'weak'
  else strength = 'negligible'
  return `${strength} ${direction}`
}

export function Correlation() {
  const defaults = defaultDates()
  const [metric, setMetric] = useState(METRICS[0].key)
  const [fromDate, setFromDate] = useState(defaults.from)
  const [toDate, setToDate] = useState(defaults.to)
  const [result, setResult] = useState<CorrelationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCorrelation({
        metric,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }, [metric, fromDate, toDate])

  const chartData = result?.data ?? []
  const pearsonR = result?.pearson_r ?? null

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Protocol Compliance vs Metric Correlation</h2>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Query Parameters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Metric</label>
              <select
                className="border rounded px-2 py-1 text-sm bg-background"
                value={metric}
                onChange={e => setMetric(e.target.value)}
              >
                {METRICS.map(m => (
                  <option key={m.key} value={m.key}>{m.label}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">From</label>
              <input
                type="date"
                className="border rounded px-2 py-1 text-sm bg-background"
                value={fromDate}
                onChange={e => setFromDate(e.target.value)}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">To</label>
              <input
                type="date"
                className="border rounded px-2 py-1 text-sm bg-background"
                value={toDate}
                onChange={e => setToDate(e.target.value)}
              />
            </div>

            <Button size="sm" onClick={fetchData} disabled={loading}>
              {loading ? 'Loading…' : 'Fetch'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {result && (
        <>
          {chartData.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No data for this metric in the selected range.
            </p>
          ) : (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  {METRICS.find(m => m.key === result.metric)?.label ?? result.metric} vs Compliance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={320}>
                  <ComposedChart data={chartData} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 11 }}
                      tickFormatter={d => d.slice(5)}
                    />
                    <YAxis
                      yAxisId="metric"
                      orientation="left"
                      tick={{ fontSize: 11 }}
                      domain={['auto', 'auto']}
                    />
                    <YAxis
                      yAxisId="compliance"
                      orientation="right"
                      tick={{ fontSize: 11 }}
                      allowDecimals={false}
                    />
                    <Tooltip contentStyle={{ fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar
                      yAxisId="compliance"
                      dataKey="compliance"
                      name="Compliance"
                      fill="#6366f1"
                      fillOpacity={0.4}
                      radius={[2, 2, 0, 0]}
                    />
                    <Line
                      yAxisId="metric"
                      type="monotone"
                      dataKey="value"
                      name={METRICS.find(m => m.key === result.metric)?.label ?? result.metric}
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {pearsonR !== null && (
            <Card>
              <CardContent className="pt-4">
                <p className="text-sm">
                  <span className="font-semibold">Correlation: </span>
                  {pearsonR.toFixed(2)}{' '}
                  <span className="text-muted-foreground">({interpretR(pearsonR)})</span>
                </p>
                {result.p_value !== null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    p-value: {result.p_value.toFixed(4)}
                    {result.p_value < 0.05 ? ' — statistically significant' : ' — not statistically significant'}
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
