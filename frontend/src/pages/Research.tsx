import { useEffect, useState } from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getResearchDigests, generateResearchDigest } from '@/lib/api'
import type { ResearchDigest } from '@/types'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })
}

export function Research() {
  const [digests, setDigests] = useState<ResearchDigest[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getResearchDigests()
      .then(setDigests)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleGenerate() {
    setGenerating(true)
    setError(null)
    try {
      const digest = await generateResearchDigest()
      setDigests(prev => [digest, ...prev])
    } catch (e: unknown) {
      setError(`Generation failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Research Digests</h2>
        <Button onClick={handleGenerate} disabled={generating}>
          {generating ? 'Generating…' : 'Generate New Digest'}
        </Button>
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {loading && <p className="text-sm text-muted-foreground">Loading…</p>}

      {!loading && digests.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">
          No digests yet. Click &apos;Generate New Digest&apos; to create the first one.
        </p>
      )}

      {digests.map(digest => (
        <Card key={digest.id}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <CardTitle className="text-base font-medium">
                {formatDate(digest.generated_at)}
              </CardTitle>
              <Badge variant="secondary">{digest.source}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{digest.summary}</p>
          </CardContent>
          {digest.interventions_mentioned.length > 0 && (
            <CardFooter className="flex flex-wrap gap-1 pt-0">
              {digest.interventions_mentioned.map(name => (
                <Badge key={name} variant="outline" className="text-xs">{name}</Badge>
              ))}
            </CardFooter>
          )}
        </Card>
      ))}
    </div>
  )
}
