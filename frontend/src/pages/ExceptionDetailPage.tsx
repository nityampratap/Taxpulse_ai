import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Sparkles,
  MessageSquare,
  CheckCircle,
  ShieldAlert,
  Building2,
  Check,
} from 'lucide-react'
import { RiskChip, StatusChip, MoneyText, EmptyState } from '../components/shared'
import { apiClient } from '../services/apiClient'

interface CaseDetail {
  id: string
  case_number: string
  status: string
  priority: string
  risk_score: string
  financial_exposure: string
  tax_impact: string
  created_at: string
  updated_at: string
  factor_breakdown?: {
    factors?: Array<{
      factor: string
      points: number
      max: number
      explanation: string
    }>
  }
  reconciliation_result?: {
    id: string
    match_type: string
    status: string
    variance_amount: string
    confidence_score: string
    reason_codes?: string[]
    evidence?: Record<string, unknown>
  }
  invoice?: {
    id: string
    number: string
    date: string
    subtotal: string
    tax_amount: string
    total_amount: string
  }
  vendor?: {
    id: string
    name: string
    risk_tier: string
  }
}

interface AIExplanation {
  summary: string
  reason: string
  evidence: string[]
  financial_impact: string
  tax_impact: string
  confidence: string
  recommended_action: string
  provider: string
  _meta?: {
    latency_ms: number
    provider_used: string
  }
}

export const ExceptionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [aiExplanation, setAiExplanation] = useState<AIExplanation | null>(null)
  const [isExplaining, setIsExplaining] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  const {
    data: caseData,
    isLoading,
    error,
  } = useQuery<CaseDetail>({
    queryKey: ['case', id],
    queryFn: () => apiClient.get<CaseDetail>(`/cases/${id}`),
    enabled: !!id,
  })

  const handleRequestAi = async () => {
    if (!id) return
    try {
      setIsExplaining(true)
      const res = await apiClient.post<AIExplanation>('/ai/explain-case', {
        case_id: id,
        prompt: 'Explain this tax discrepancy case with root cause and recommended action.',
      })
      setAiExplanation(res)
    } catch (err) {
      console.error('Failed to get AI explanation:', err)
    } finally {
      setIsExplaining(false)
    }
  }

  const handleReview = async () => {
    if (!id) return
    try {
      setActionLoading('review')
      await apiClient.post(`/cases/${id}/review`, { notes: 'Marked in review via dashboard' })
      setActionSuccess('Case status updated to IN_REVIEW')
      await queryClient.invalidateQueries({ queryKey: ['case', id] })
      await queryClient.invalidateQueries({ queryKey: ['cases'] })
    } catch (err) {
      console.error('Failed to transition case:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleResolve = async () => {
    if (!id) return
    try {
      setActionLoading('resolve')
      await apiClient.post(`/cases/${id}/resolve`, { notes: 'Resolved by analyst' })
      setActionSuccess('Case successfully marked as RESOLVED')
      await queryClient.invalidateQueries({ queryKey: ['case', id] })
      await queryClient.invalidateQueries({ queryKey: ['cases'] })
    } catch (err) {
      console.error('Failed to resolve case:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleSendWhatsApp = async () => {
    if (!id) return
    try {
      setActionLoading('whatsapp')
      await apiClient.post('/whatsapp/send', {
        case_id: id,
        phone: '+919876543210',
      })
      setActionSuccess('WhatsApp alert sent to +919876543210. Check the WhatsApp channel!')
    } catch (err) {
      console.error('Failed to send WhatsApp alert:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const evidence = caseData?.reconciliation_result?.evidence || {}
  const factors = caseData?.factor_breakdown?.factors || []

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/exceptions')}
            className="p-1.5 rounded-md hover:bg-slate-200 text-slate-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                Case {caseData?.case_number || id}
              </h1>
              {caseData && (
                <>
                  <RiskChip
                    tier={caseData.priority}
                    score={parseFloat(caseData.risk_score)}
                  />
                  <StatusChip status={caseData.status} />
                </>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Exception Ticket • Case ID: <span className="font-mono">{caseData?.id || id}</span>
            </p>
          </div>
        </div>

        {actionSuccess && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-md">
            <Check className="w-3.5 h-3.5 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-slate-500 font-medium">
          Loading case details...
        </div>
      ) : error || !caseData ? (
        <EmptyState
          title="Case Not Found"
          description={`No case records found for ID "${id}".`}
          action={{
            label: 'Back to Exceptions',
            onClick: () => navigate('/exceptions'),
          }}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Discrepancy Details & AI Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* Discrepancy Details Card */}
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                Discrepancy Breakdown
              </h2>
              <span className="text-xs text-slate-400 font-mono">
                Match: {caseData.reconciliation_result?.match_type || 'N/A'}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg border border-slate-100">
              <div>
                <span className="text-[11px] text-slate-500 block uppercase font-medium">Vendor</span>
                <span className="text-sm font-semibold text-slate-800 flex items-center gap-1.5 mt-0.5">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  {caseData.vendor?.name || 'Unknown Vendor'}
                </span>
                {caseData.vendor?.risk_tier && (
                  <span className="text-[10px] text-slate-400">Risk: {caseData.vendor.risk_tier}</span>
                )}
              </div>

              <div>
                <span className="text-[11px] text-slate-500 block uppercase font-medium">Invoice Number</span>
                <span className="text-sm font-semibold font-mono text-slate-800 mt-0.5 block">
                  {caseData.invoice?.number || (evidence['invoice_number'] as string) || 'N/A'}
                </span>
                <span className="text-[10px] text-slate-400">
                  {caseData.invoice?.date || (evidence['invoice_date'] as string) || '—'}
                </span>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 block uppercase font-medium">Tax Impact</span>
                <span className="text-sm font-semibold text-rose-600 mt-0.5 block">
                  <MoneyText amount={parseFloat(caseData.tax_impact)} />
                </span>
                <span className="text-[10px] text-slate-400">Statutory Variance</span>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 block uppercase font-medium">Gross Exposure</span>
                <span className="text-sm font-semibold text-slate-800 mt-0.5 block">
                  <MoneyText amount={parseFloat(caseData.financial_exposure)} />
                </span>
                <span className="text-[10px] text-slate-400">Total Transaction</span>
              </div>
            </div>

            {/* Evidence & Calculation Details */}
            {Object.keys(evidence).length > 0 && (
              <div className="pt-2">
                <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                  Statutory Calculation Evidence
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  {Object.entries(evidence).map(([key, val]) => (
                    <div key={key} className="p-2 bg-slate-50 rounded border border-slate-100">
                      <span className="text-slate-400 block text-[10px] uppercase font-mono">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="font-medium text-slate-800 font-mono">
                        {typeof val === 'number' && key.includes('rate')
                          ? `${(val * 100).toFixed(1)}%`
                          : typeof val === 'number'
                          ? val.toLocaleString('en-IN')
                          : String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Factor Breakdown */}
            {factors.length > 0 && (
              <div className="pt-2">
                <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                  Risk Factor Matrix ({caseData.risk_score} pts)
                </h3>
                <div className="space-y-1.5">
                  {factors.map((f, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-100 text-xs"
                    >
                      <span className="font-medium text-slate-700">
                        {f.explanation || f.factor}
                      </span>
                      <span className="font-mono text-slate-500 font-semibold">
                        {f.points} / {f.max} pts
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI Copilot Explanation Card */}
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                AI Copilot Root Cause Analysis
              </h2>
              {aiExplanation && (
                <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono font-medium">
                  {aiExplanation.provider} Provider
                  {aiExplanation._meta?.latency_ms ? ` (${aiExplanation._meta.latency_ms}ms)` : ''}
                </span>
              )}
            </div>

            {!aiExplanation ? (
              <EmptyState
                icon={<Sparkles className="w-6 h-6 stroke-[1.5] text-blue-500" />}
                title="AI Analysis Available"
                description="Click Request AI Analysis to inspect the discrepancy against statutory GST/VAT rules, calculate exact variances, and propose resolution steps."
                action={{
                  label: isExplaining ? 'Analyzing Discrepancy...' : 'Request AI Analysis',
                  onClick: handleRequestAi,
                }}
                className="border-dashed py-8 shadow-none"
              />
            ) : (
              <div className="space-y-3 text-sm">
                <div className="p-3.5 bg-blue-50/60 rounded-md border border-blue-100">
                  <span className="text-xs font-bold text-blue-900 block mb-1 uppercase tracking-wide">
                    Executive Summary
                  </span>
                  <p className="text-slate-800 leading-relaxed">{aiExplanation.summary}</p>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-md border border-slate-100 space-y-2">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-0.5">
                      Identified Root Cause
                    </span>
                    <p className="text-slate-700">{aiExplanation.reason}</p>
                  </div>

                  <div className="pt-2 border-t border-slate-200/60">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-0.5">
                      Recommended Next Step
                    </span>
                    <p className="text-emerald-700 font-medium">
                      {aiExplanation.recommended_action}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleRequestAi}
                  disabled={isExplaining}
                  className="text-xs text-blue-600 hover:underline inline-flex items-center gap-1 font-medium pt-1"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {isExplaining ? 'Re-analyzing...' : 'Refresh AI Analysis'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Workflow Actions */}
        <div className="space-y-6">
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Reviewer Actions
            </h3>

            <div className="space-y-2.5">
              {caseData.status === 'OPEN' && (
                <button
                  type="button"
                  onClick={handleReview}
                  disabled={!!actionLoading}
                  className="w-full flex items-center justify-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  {actionLoading === 'review' ? 'Updating...' : 'Mark In Review'}
                </button>
              )}

              {caseData.status !== 'RESOLVED' && (
                <button
                  type="button"
                  onClick={handleResolve}
                  disabled={!!actionLoading}
                  className="w-full flex items-center justify-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-md text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm transition-colors disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                  {actionLoading === 'resolve' ? 'Resolving...' : 'Resolve Discrepancy'}
                </button>
              )}

              <button
                type="button"
                onClick={handleSendWhatsApp}
                disabled={!!actionLoading}
                className="w-full flex items-center justify-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-md text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 shadow-sm transition-colors disabled:opacity-50"
              >
                <MessageSquare className="w-4 h-4 text-emerald-600" />
                {actionLoading === 'whatsapp' ? 'Sending Alert...' : 'Dispatch WhatsApp Alert'}
              </button>
            </div>

            <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400 space-y-1">
              <div>Created: {caseData.created_at}</div>
              <div>Last Updated: {caseData.updated_at}</div>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  )
}

export default ExceptionDetailPage
