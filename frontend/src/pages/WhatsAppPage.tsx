import React, { useState } from 'react'
import { EmptyState, StatusChip } from '../components/shared'
import { MessageSquare, Send, ShieldAlert } from 'lucide-react'

export const WhatsAppPage: React.FC = () => {
  const [messages] = useState<unknown[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isSending, setIsSending] = useState(false)

  const handleSendSimulation = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim()) return
    setIsSending(true)
    setTimeout(() => {
      setIsSending(false)
      setInputMessage('')
    }, 400)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">WhatsApp Review Channel</h1>
          <p className="text-sm text-slate-500 mt-1">
            Human-in-the-loop dispute alerts, conversational explanation, and guarded confirmation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <StatusChip status="ACTIVE" label="Webhook Connected" />
        </div>
      </div>

      {/* Safety Guardrail Callout */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
        <div>
          <span className="font-semibold">Statutory Accounting Guardrail:</span> WhatsApp interactions can only transition case states (e.g. to <code className="font-mono bg-blue-100 px-1 py-0.5 rounded text-blue-900">RESOLVED</code>) after an explicit, time-limited <code className="font-mono bg-blue-100 px-1 py-0.5 rounded text-blue-900">CONFIRM &lt;CODE&gt;</code> prompt. It cannot mutate accounting ledger records.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Message Log */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm min-h-[380px] flex flex-col justify-between">
            <h2 className="text-base font-semibold text-slate-900 mb-3">Conversation Stream</h2>

            {messages.length === 0 ? (
              <EmptyState
                icon={<MessageSquare className="w-6 h-6 stroke-[1.5]" />}
                title="No WhatsApp Messages Yet"
                description="Outbound alerts and simulated inbound replies will appear in this real-time stream."
                className="border-0 shadow-none my-auto"
              />
            ) : null}

            {/* Inbound Simulator Input */}
            <form onSubmit={handleSendSimulation} className="pt-4 border-t border-slate-100 flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Simulate reviewer reply: EXPLAIN, REVIEW, or CONFIRM 8472..."
                className="flex-1 px-3 py-2 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={isSending || !inputMessage.trim()}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </form>
          </div>
        </div>

        {/* Right: Quick Action Controls */}
        <div className="space-y-4">
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-3">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Simulation Shortcuts
            </h3>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setInputMessage('EXPLAIN')}
                className="w-full text-left px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded hover:bg-slate-100 transition-colors flex items-center justify-between"
              >
                <span>Request Case Analysis</span>
                <span className="font-mono text-slate-400">EXPLAIN</span>
              </button>
              <button
                type="button"
                onClick={() => setInputMessage('REVIEW')}
                className="w-full text-left px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded hover:bg-slate-100 transition-colors flex items-center justify-between"
              >
                <span>Initiate Token Sign-Off</span>
                <span className="font-mono text-slate-400">REVIEW</span>
              </button>
              <button
                type="button"
                onClick={() => setInputMessage('CONFIRM 8472')}
                className="w-full text-left px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded hover:bg-slate-100 transition-colors flex items-center justify-between"
              >
                <span>Execute Final Resolution</span>
                <span className="font-mono text-slate-400">CONFIRM 8472</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
