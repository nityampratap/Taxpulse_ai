import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Sparkles, MessageSquare, CheckCircle, ShieldAlert } from 'lucide-react'
import { RiskChip, StatusChip, EmptyState } from '../components/shared'

export const ExceptionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
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
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Case {id}</h1>
            <RiskChip tier="HIGH" score={62} />
            <StatusChip status="OPEN" />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Exception Ticket • Case ID: <span className="font-mono">{id}</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Case Overview & Breakdown */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              Discrepancy Details
            </h2>

            <EmptyState
              title="Awaiting API Case Data"
              description={`Detailed discrepancy records for case ${id} will populate when the backend API is connected.`}
              className="border-dashed py-8 shadow-none"
            />
          </div>

          {/* AI Copilot Explanation Drawer / Card */}
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                AI Copilot Root Cause Analysis
              </h2>
              <span className="text-xs text-slate-400 font-mono">Isolated Context</span>
            </div>

            <EmptyState
              title="No AI Explanation Generated"
              description="Click Request AI Analysis to send the structured case payload to the LLM Copilot."
              action={{
                label: 'Request AI Analysis',
                onClick: () => {},
              }}
              className="border-dashed py-8 shadow-none"
            />
          </div>
        </div>

        {/* Right Column: Workflow Actions & Stored Factor Matrix */}
        <div className="space-y-6">
          <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-3">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Reviewer Actions
            </h3>
            <div className="space-y-2">
              <button
                type="button"
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold rounded-md text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Mark In Review
              </button>
              <button
                type="button"
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold rounded-md text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 shadow-sm transition-colors"
              >
                <MessageSquare className="w-4 h-4" />
                Dispatch WhatsApp Alert
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
