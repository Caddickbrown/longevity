import { useEffect, useState } from 'react'
import type { BeliefSnapshot } from '@/types'
import { createBeliefSnapshot, getBeliefSnapshots } from '@/lib/api'

type GroupedBelief = { title: string; versions: BeliefSnapshot[] }

export function Beliefs() {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tags, setTags] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [groups, setGroups] = useState<GroupedBelief[]>([])
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  async function loadBeliefs() {
    const all = await getBeliefSnapshots()
    const map = new Map<string, BeliefSnapshot[]>()
    for (const s of all) {
      const arr = map.get(s.title) ?? []
      arr.push(s)
      map.set(s.title, arr)
    }
    setGroups(
      Array.from(map.entries()).map(([t, versions]) => ({
        title: t,
        versions: versions.sort(
          (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        ),
      }))
    )
  }

  useEffect(() => { loadBeliefs() }, [])

  async function handleSave() {
    if (!title.trim() || !body.trim()) return
    setSaving(true)
    try {
      await createBeliefSnapshot({
        title: title.trim(),
        body: body.trim(),
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      })
      setSaved(true)
      setTitle('')
      setBody('')
      setTags('')
      await loadBeliefs()
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  function toggleExpand(t: string) {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(t) ? next.delete(t) : next.add(t)
      return next
    })
  }

  return (
    <div className="max-w-2xl space-y-8">
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Record a Belief</h2>
        <div className="space-y-2">
          <label htmlFor="belief-title" className="block text-sm font-medium">Title</label>
          <input
            id="belief-title"
            className="border rounded px-2 py-1 text-sm w-full"
            placeholder="e.g. On sleep, On relationships"
            value={title}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="belief-body" className="block text-sm font-medium">Belief</label>
          <textarea
            id="belief-body"
            rows={5}
            className="border rounded px-3 py-2 text-sm w-full resize-y"
            placeholder="Write your current belief..."
            value={body}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBody(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="belief-tags" className="block text-sm font-medium">Tags (comma-separated)</label>
          <input
            id="belief-tags"
            className="border rounded px-2 py-1 text-sm w-full"
            placeholder="e.g. health, mindset"
            value={tags}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTags(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving || !title.trim() || !body.trim()}
            className="bg-primary text-primary-foreground rounded px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Belief'}
          </button>
          {saved && <span className="text-sm text-green-600">Saved ✓</span>}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">All Beliefs</h2>
        {groups.length === 0 && (
          <p className="text-sm text-muted-foreground">No beliefs recorded yet.</p>
        )}
        {groups.map(({ title: t, versions }) => {
          const latest = versions[versions.length - 1]
          const isOpen = expanded.has(t)
          return (
            <div key={t} className="border rounded-lg p-4 space-y-2 cursor-pointer" onClick={() => toggleExpand(t)}>
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{t}</h3>
                <span className="text-xs text-muted-foreground">
                  {versions.length} version{versions.length !== 1 ? 's' : ''} {isOpen ? '▲' : '▼'}
                </span>
              </div>
              {!isOpen && (
                <p className="text-sm text-muted-foreground line-clamp-2">{latest.body}</p>
              )}
              {isOpen && (
                <div className="space-y-4 pt-2">
                  {versions.map(v => (
                    <div key={v.id} className="space-y-1 border-t pt-3 first:border-t-0 first:pt-0">
                      <p className="text-xs text-muted-foreground">
                        {new Date(v.created_at).toLocaleString()}
                        {v.tags.length > 0 && ` · ${v.tags.join(', ')}`}
                      </p>
                      <p className="text-sm whitespace-pre-wrap">{v.body}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </section>
    </div>
  )
}
