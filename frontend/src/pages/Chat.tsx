import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { sendChatMessage, getChatHistory, clearChatHistory } from '@/lib/api'
import type { ConversationMessage } from '@/types'

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

interface ThinkingBubble {
  id: 'thinking'
  role: 'assistant'
  content: ''
  created_at: string
}

type DisplayMessage = ConversationMessage | ThinkingBubble

export function Chat() {
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmClear, setConfirmClear] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getChatHistory()
      .then(setMessages)
      .catch(() => setError('Failed to load chat history.'))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    const optimisticUser: ConversationMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }

    setMessages(prev => [...prev, optimisticUser])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const reply = await sendChatMessage(text)
      setMessages(prev => {
        // replace the optimistic user message with confirmed if id changed, else just append reply
        return [...prev, reply]
      })
    } catch (err: unknown) {
      const status = (err as { status?: number }).status
      if (status === 503) {
        setError('Chat is unavailable: no API key configured on the server.')
      } else {
        setError((err as Error).message ?? 'Failed to send message.')
      }
      // Remove the optimistic user message on error
      setMessages(prev => prev.filter(m => m.id !== optimisticUser.id))
      setInput(text)
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  async function handleClearHistory() {
    if (!confirmClear) {
      setConfirmClear(true)
      return
    }
    try {
      await clearChatHistory()
      setMessages([])
      setError(null)
    } catch {
      setError('Failed to clear history.')
    } finally {
      setConfirmClear(false)
    }
  }

  const displayMessages: DisplayMessage[] = loading
    ? [...messages, { id: 'thinking' as const, role: 'assistant' as const, content: '', created_at: new Date().toISOString() }]
    : messages

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 160px)' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Digital Continuity</h2>
        <div className="flex items-center gap-2">
          {confirmClear && (
            <span className="text-sm text-muted-foreground">Are you sure?</span>
          )}
          <Button
            variant={confirmClear ? 'destructive' : 'outline'}
            size="sm"
            onClick={handleClearHistory}
            onBlur={() => setTimeout(() => setConfirmClear(false), 200)}
          >
            {confirmClear ? 'Confirm Clear' : 'Clear History'}
          </Button>
          {confirmClear && (
            <Button variant="outline" size="sm" onClick={() => setConfirmClear(false)}>
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-3 rounded-md bg-destructive/10 border border-destructive/30 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Message area */}
      <div className="flex-1 overflow-y-auto rounded-lg border bg-muted/20 p-4 flex flex-col gap-3">
        {displayMessages.length === 0 && !loading ? (
          <div className="flex flex-1 items-center justify-center text-muted-foreground text-sm">
            No conversation yet. Say hello to get started.
          </div>
        ) : (
          displayMessages.map((msg, idx) => {
            const isUser = msg.role === 'user'
            const isThinking = msg.id === 'thinking'

            return (
              <div
                key={isThinking ? `thinking-${idx}` : msg.id}
                className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}
              >
                <span className="text-xs text-muted-foreground px-1">
                  {isUser ? 'You' : 'Digital Continuity'}
                  {!isThinking && <span className="ml-2">{formatTime(msg.created_at)}</span>}
                </span>
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                    isUser
                      ? 'bg-primary text-primary-foreground rounded-br-sm'
                      : 'bg-muted text-foreground rounded-bl-sm'
                  }`}
                >
                  {isThinking ? (
                    <span className="italic text-muted-foreground">Thinking…</span>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            )
          })
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="mt-3 flex gap-2 items-end">
        <Textarea
          className="flex-1 resize-none min-h-[44px] max-h-[120px]"
          rows={1}
          placeholder={loading ? 'Waiting for response…' : 'Type a message… (Enter to send, Shift+Enter for newline)'}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <Button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="shrink-0"
        >
          Send
        </Button>
      </div>
    </div>
  )
}
