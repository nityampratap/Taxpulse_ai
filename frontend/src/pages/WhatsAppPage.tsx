import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { EmptyState, StatusChip } from '../components/shared'
import { MessageSquare, Send, ShieldAlert, Check } from 'lucide-react'
import { apiClient } from '../services/apiClient'

interface WhatsAppMessage {
  id: string
  direction: 'INBOUND' | 'OUTBOUND'
  message_body: string
  status: string
  phone: string
  sent_at: string
  case_id?: string
}

export const WhatsAppPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [inputMessage, setInputMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [notification, setNotification] = useState<string | null>(null)

  const { data: messages = [], isLoading } = useQuery<WhatsAppMessage[]>({
    queryKey: ['whatsapp', 'conversations'],
    queryFn: () => apiClient.get<WhatsAppMessage[]>('/whatsapp/conversations'),
    refetchInterval: 3000,
  })

  const sendSimulation = async (text: string) => {
    if (!text.trim()) return
    try {
      setIsSending(true)
      const res = await apiClient.post<{ response: string }>('/whatsapp/simulate-inbound', {
        phone: '+919876543210',
        message: text.trim(),
      })
      setInputMessage('')
      if (res.response) {
        setNotification(`Simulated reply processed: "${res.response.substring(0, 60)}..."`)
      }
      await queryClient.invalidateQueries({ queryKey: ['whatsapp'] })
      await queryClient.invalidateQueries({ queryKey: ['cases'] })
    } catch (err) {
      console.error('Failed to simulate WhatsApp message:', err)
    } finally {
      setIsSending(false)
    }
  }

  const handleSendSimulation = (e: React.FormEvent) => {
    e.preventDefault()
    sendSimulation(inputMessage)
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

      {notification && (
        <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg">
          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Message Log */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm min-h-[440px] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
                <h2 className="text-base font-semibold text-slate-900">Conversation Stream</h2>
                <span className="text-xs text-slate-400 font-mono">{messages.length} messages</span>
              </div>

              {messages.length === 0 && !isLoading ? (
                <EmptyState
                  icon={<MessageSquare className="w-6 h-6 stroke-[1.5]" />}
                  title="No WhatsApp Messages Yet"
                  description="Dispatched alerts from the Exceptions page and simulated inbound replies will appear in this real-time stream."
                  className="border-0 shadow-none my-12"
                />
              ) : (
                <div className="space-y-3 max-h-[380px] overflow-y-auto pr-2">
                  {messages.map((m) => {
                    const isOutbound = m.direction === 'OUTBOUND'
                    return (
                      <div
                        key={m.id}
                        className={`flex flex-col ${isOutbound ? 'items-start' : 'items-end'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-lg p-3 text-xs leading-relaxed ${
                            isOutbound
                              ? 'bg-slate-100 text-slate-800 border border-slate-200'
                              : 'bg-emerald-600 text-white shadow-sm'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-3 text-[10px] mb-1 opacity-75 font-mono">
                            <span>{isOutbound ? 'TaxPulse Bot' : m.phone || 'Reviewer'}</span>
                            <span>{m.sent_at}</span>
                          </div>
                          <div className="whitespace-pre-wrap">{m.message_body}</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

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
            <p className="text-xs text-slate-500">
              Click any shortcut to instantly test the guarded conversational state machine:
            </p>
            <div className="space-y-2 pt-1">
              <button
                type="button"
                onClick={() => sendSimulation('EXPLAIN')}
                disabled={isSending}
                className="w-full text-left px-3 py-2.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded hover:bg-slate-100 transition-colors flex items-center justify-between"
              >
                <div>
                  <span className="font-semibold text-slate-800 block">Request Case Analysis</span>
                  <span className="text-[11px] text-slate-500">Inspect discrepancy details & root cause</span>
                </div>
                <span className="font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded text-[11px]">EXPLAIN</span>
              </button>

              <button
                type="button"
                onClick={() => sendSimulation('REVIEW')}
                disabled={isSending}
                className="w-full text-left px-3 py-2.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded hover:bg-slate-100 transition-colors flex items-center justify-between"
              >
                <div>
                  <span className="font-semibold text-slate-800 block">Initiate Resolution</span>
                  <span className="text-[11px] text-slate-500">Generates 4-digit confirmation token</span>
                </div>
                <span className="font-mono text-amber-600 bg-amber-50 px-2 py-0.5 rounded text-[11px]">REVIEW</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  const promptCode = window.prompt('Enter confirmation code from WhatsApp message (e.g. 8472):', '')
                  if (promptCode) sendSimulation(`CONFIRM ${promptCode.trim()}`)
                }}
                disabled={isSending}
                className="w-full text-left px-3 py-2.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded hover:bg-slate-100 transition-colors flex items-center justify-between"
              >
                <div>
                  <span className="font-semibold text-slate-800 block">Guarded Sign-Off</span>
                  <span className="text-[11px] text-slate-500">Submit CONFIRM &lt;CODE&gt; to resolve</span>
                </div>
                <span className="font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded text-[11px]">CONFIRM</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WhatsAppPage

