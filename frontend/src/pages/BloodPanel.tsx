import { useRef, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { importBloodPanel } from '@/lib/api'

export function BloodPanel() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ inserted: number; skipped: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const [exportLoading, setExportLoading] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const data = await importBloodPanel(file)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleExport() {
    setExportLoading(true)
    setExportError(null)
    try {
      const res = await fetch('/export')
      if (!res.ok) throw new Error(`Export failed: ${res.status} ${res.statusText}`)
      const blob = await res.blob()
      const today = new Date().toISOString().slice(0, 10)
      const filename = `longevity-export-${today}.json`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExportLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-md">
      <Card>
        <CardHeader>
          <CardTitle>Import Blood Panel</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Upload a CSV export from Medichecks or Thriva. Columns required:{' '}
            <code className="text-xs">Test, Value, Unit, Reference Range, Date</code>
          </p>
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              onChange={handleUpload}
              disabled={loading}
              className="text-sm file:mr-3 file:rounded file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-sm file:font-medium"
            />
            {loading && <span className="text-sm text-muted-foreground">Uploading…</span>}
          </div>
          {result && (
            <p className="text-sm text-green-600">
              Imported {result.inserted} readings
              {result.skipped > 0 && ` (${result.skipped} duplicates skipped)`}
            </p>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Export All Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Download a complete JSON snapshot of all your data — biomarkers, journal, beliefs,
            protocols, and research digests.
          </p>
          <Button onClick={handleExport} disabled={exportLoading}>
            {exportLoading ? 'Downloading…' : 'Download Export'}
          </Button>
          {exportError && <p className="text-sm text-destructive">{exportError}</p>}
          <p className="text-xs text-muted-foreground">
            This file is for local backup and future AI persona construction.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
