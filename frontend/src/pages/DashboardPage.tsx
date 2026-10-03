import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { StatCard, EmptyState, DataTable, type Column, MoneyText, StatusChip, RiskChip } from '../components/shared'
import { TrendingUp, AlertCircle, CheckCircle2, DollarSign, Play } from 'lucide-react'
import { apiClient } from '../services/apiClient'
import { useNavigate } from 'react-router-dom'

interface CaseItem {
  id: string
  case_number: string
  status: string
  priority: string
  risk_score: string
  financial_exposure: string
  tax_impact: string
  vendor?: string | { name?: string; id?: string; risk_tier?: string }
}

interface DashboardMetrics {
  invoices_count?: number
  runs_count?: number
  total_transactions: number
  matched: number
  unmatched: number
  duplicates: number
  missing: number
  tax_variance: string
  potential_exposure: string
  critical: number
  high_risk: number
  anomalies: number
}

export const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRunningReconciliation, setIsRunningReconciliation] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const { data: metrics, isLoading: isMetricsLoading } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard', 'metrics'],
    queryFn: () => apiClient.get<DashboardMetrics>('/dashboard/metrics'),
  })

  const { data: casesData, isLoading: isCasesLoading, error: casesError } = useQuery<{ cases?: CaseItem[] } | CaseItem[]>({
    queryKey: ['cases'],
    queryFn: () => apiClient.get<{ cases?: CaseItem[] } | CaseItem[]>('/cases'),
  })

  const handleGenerateDemoData = async () => {
    try {
      setIsGenerating(true)
      await apiClient.post('/demo/generate')
      setStatusMessage('Demo dataset loaded! Click "Run reconciliation" to match transactions and analyze discrepancies.')
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      await queryClient.invalidateQueries({ queryKey: ['cases'] })
    } catch (err: unknown) {
      console.error('Failed to generate demo data:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleRunReconciliation = async () => {
    try {
      setIsRunningReconciliation(true)
      await apiClient.post('/reconciliation/run', {})
      setStatusMessage('Reconciliation completed! Discrepancy cases and risk scores are ready for review.')
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      await queryClient.invalidateQueries({ queryKey: ['cases'] })
    } catch (err: unknown) {
      console.error('Failed to run reconciliation:', err)
    } finally {
      setIsRunningReconciliation(false)
    }
  }

  const cases: CaseItem[] = Array.isArray(casesData)
    ? casesData
    : (casesData as unknown as { cases?: CaseItem[] })?.cases || []

  const total = metrics?.total_transactions || 0
  const matched = metrics?.matched || 0
  const matchRate = total > 0 ? `${((matched / total) * 100).toFixed(1)}%` : '—'
  const exposureNum = parseFloat(metrics?.potential_exposure || '0')
  const varianceNum = parseFloat(metrics?.tax_variance || '0')
  const highRiskCount = (metrics?.high_risk || 0) + (metrics?.critical || 0)

  const invoicesCount = metrics?.invoices_count ?? 0
  const runsCount = metrics?.runs_count ?? 0

  // Data-aware empty state resolution
  let emptyTitle = 'No Reconciliation Data'
  let emptyDesc = 'No financial records imported yet. Generate demo dataset to load invoices, payments, and ledger entries.'
  let emptyAction: { label: string; onClick: () => void } | undefined = {
    label: isGenerating ? 'Generating demo data...' : 'Generate demo data',
    onClick: handleGenerateDemoData,
  }

  if (invoicesCount === 0) {
    emptyTitle = 'No Reconciliation Data'
    emptyDesc = statusMessage || 'No financial records imported yet. Generate demo dataset to load invoices, payments, and ledger entries.'
    emptyAction = {
      label: isGenerating ? 'Generating demo data...' : 'Generate demo data',
      onClick: handleGenerateDemoData,
    }
  } else if (runsCount === 0) {
    emptyTitle = 'Dataset Ready for Reconciliation'
    emptyDesc = statusMessage || 'Financial records loaded into ledger. Execute reconciliation engine to match transactions and detect tax variances.'
    emptyAction = {
      label: isRunningReconciliation ? 'Running reconciliation...' : 'Run reconciliation',
      onClick: handleRunReconciliation,
    }
  } else {
    emptyTitle = 'No Discrepancies Found'
    emptyDesc = 'All reconciliations matched within tolerance. Zero exception cases or tax variances detected.'
    emptyAction = undefined
  }

  const columns: Column<CaseItem>[] = [
    {
      key: 'case_number',
      header: 'Case #',
      render: (item) => (
        <span
          className="font-mono font-medium text-emerald-700 hover:underline cursor-pointer"
          onClick={() => navigate(`/exceptions/${item.case_number}`)}
        >
          {item.case_number}
        </span>
      ),
    },
    {
      key: 'vendor',
      header: 'Vendor',
      render: (item) => {
        if (!item.vendor) return '—'
        if (typeof item.vendor === 'object' && item.vendor !== null) {
          return (item.vendor as { name?: string }).name || '—'
        }
        return String(item.vendor)
      },
    },
    {
      key: 'financial_exposure',
      header: 'Exposure',
      align: 'right',
      render: (item) => <MoneyText amount={parseFloat(item.financial_exposure)} />,
    },
    {
      key: 'tax_impact',
      header: 'Tax Impact',
      align: 'right',
      render: (item) => <MoneyText amount={parseFloat(item.tax_impact)} />,
    },
    {
      key: 'priority',
      header: 'Risk Tier',
      render: (item) => <RiskChip tier={item.priority} score={parseFloat(item.risk_score)} />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (item) => <StatusChip status={item.status} />,
    },
  ]

  const isLoading = isMetricsLoading || isCasesLoading

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Dashboard Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Autonomous tax reconciliation metrics and risk intelligence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {invoicesCount === 0 && (
            <button
              type="button"
              onClick={handleGenerateDemoData}
              disabled={isGenerating}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 rounded-md hover:bg-slate-800 shadow-sm transition-colors disabled:opacity-50"
            >
              {isGenerating ? 'Generating...' : 'Generate Demo Data'}
            </button>
          )}
          {invoicesCount > 0 && (
            <button
              type="button"
              onClick={handleRunReconciliation}
              disabled={isRunningReconciliation}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-700 rounded-md hover:bg-emerald-800 shadow-sm transition-colors disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {isRunningReconciliation ? 'Running Reconciliation...' : 'Run Reconciliation'}
            </button>
          )}
        </div>
      </div>

      {/* Metric Cards - Live metrics from DB queries */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Financial Exposure"
          value={<MoneyText amount={exposureNum} />}
          subtitle="Awaiting reconciliation"
          icon={<DollarSign className="w-4 h-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Tax Discrepancy Variance"
          value={<MoneyText amount={varianceNum} />}
          subtitle="Statutory risk detected"
          icon={<AlertCircle className="w-4 h-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Auto-Match Rate"
          value={matchRate}
          subtitle="Deterministic & fuzzy"
          icon={<CheckCircle2 className="w-4 h-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="High Risk Cases"
          value={String(highRiskCount)}
          subtitle="SLA escalated items"
          icon={<TrendingUp className="w-4 h-4" />}
          isLoading={isLoading}
        />
      </div>

      {/* Main Table Container */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Priority Tax Discrepancies</h2>
          <span className="text-xs text-slate-400 font-mono">{cases.length} items pending</span>
        </div>

        {cases.length === 0 && !isLoading && !casesError ? (
          <EmptyState
            title={emptyTitle}
            description={emptyDesc}
            action={emptyAction}
          />
        ) : (
          <DataTable
            columns={columns}
            data={cases}
            isLoading={isLoading}
            error={casesError ? { code: 'QUERY_ERROR', message: String(casesError) } : null}
            emptyTitle={emptyTitle}
            emptyDescription={emptyDesc}
          />
        )}
      </div>
    </div>
  )
}

export default DashboardPage
