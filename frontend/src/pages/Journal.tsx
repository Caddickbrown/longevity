import { useState, useEffect, useCallback } from 'react'
import { upsertJournalEntry, getJournalEntries, getJournalEntry } from '@/lib/api'
import type { JournalEntry } from '@/types'

const today = () => new Date().toISOString().slice(0, 10)

export function Journal() {
  const [date, setDate] = useState(today())
  const [body, setBody] = useState('')
  const [mood, setMood] = useState(5)
  const [energy, setEnergy] = useState(5)
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [saved, setSaved] = useState(false)
  const [entries, setEntries] = useState<JournalEntry[]>([])

  const loadEntry = useCallback((entry: JournalEntry) => {
    setDate(entry.date)
    setBody(entry.body)
    setMood(entry.mood ?? 5)
    setEnergy(entry.energy ?? 5)
    setTags(entry.tags ?? [])
    setTagInput('')
  }, [])

  useEffect(() => {
    getJournalEntries().then(setEntries).catch(() => {})
    getJournalEntry(today()).then(loadEntry).catch(() => {})
  }, [loadEntry])

  const handleSave = async () => {
    const entry = await upsertJournalEntry({ date, body, tags, mood, energy })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
    setEntries(prev => {
      const idx = prev.findIndex(e => e.date === entry.date)
      return idx >= 0 ? prev.map((e, i) => (i === idx ? entry : e)) : [entry, ...prev]
    })
  }

  const addTag = (value: string) => {
    const newTags = value.split(',').map(t => t.trim()).filter(Boolean)
    setTags(prev => [...new Set([...prev, ...newTags])])
    setTagInput('')
  }

  const removeTag = (tag: string) => setTags(prev => prev.filter(t => t !== tag))

  return (
    <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
      {/* Editor column */}
      <div style={{ flex: '3 1 380px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h2 className="text-lg font-semibold">Journal</h2>

        <div>
          <label className="block text-sm font-medium mb-1">Date</label>
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Entry</label>
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            rows={8}
            className="border rounded px-3 py-2 text-sm w-full resize-y"
            placeholder="Write your journal entry…"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Mood <span className="ml-2 font-mono">{mood}</span></label>
          <input
            type="range" min={1} max={10} value={mood}
            onChange={e => setMood(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Energy <span className="ml-2 font-mono">{energy}</span></label>
          <input
            type="range" min={1} max={10} value={energy}
            onChange={e => setEnergy(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Tags</label>
          <input
            type="text"
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addTag(tagInput) } }}
            onBlur={() => { if (tagInput) addTag(tagInput) }}
            placeholder="Add tags, comma-separated"
            className="border rounded px-2 py-1 text-sm w-full"
          />
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {tags.map(tag => (
                <span key={tag} className="inline-flex items-center gap-1 bg-muted text-xs rounded px-2 py-0.5">
                  {tag}
                  <button onClick={() => removeTag(tag)} className="hover:text-destructive">×</button>
                </span>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={handleSave}
          className="self-start bg-primary text-primary-foreground rounded px-4 py-2 text-sm font-medium hover:opacity-90"
        >
          {saved ? 'Saved ✓' : 'Save Entry'}
        </button>
      </div>

      {/* History column */}
      <div style={{ flex: '2 1 260px' }}>
        <h2 className="text-lg font-semibold mb-3">Recent Entries</h2>
        {entries.length === 0 && <p className="text-sm text-muted-foreground">No entries yet.</p>}
        <ul className="flex flex-col gap-2">
          {entries.slice(0, 30).map(entry => (
            <li
              key={entry.date}
              onClick={() => loadEntry(entry)}
              className="cursor-pointer border rounded p-2 text-sm hover:bg-muted transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold">{entry.date}</span>
                <span className="text-xs text-muted-foreground">
                  {entry.mood != null && <>M:{entry.mood} </>}
                  {entry.energy != null && <>E:{entry.energy}</>}
                </span>
              </div>
              <p className="text-muted-foreground truncate">{entry.body.slice(0, 80)}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
