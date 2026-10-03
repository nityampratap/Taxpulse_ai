import React, { useState } from 'react'
import { StatCard, EmptyState, DataTable, type Column, MoneyText, StatusChip, RiskChip } from '../components/shared'
import { TrendingUp, AlertCircle, CheckCircle2, DollarSign } from 'lucide-react'
import { apiClient } from '../services/apiClient'

interface DashboardMetricItem {
  id: string
  caseNumber: string
  vendor: string
  exposure: number
  variance: number
  status: string
  risk: string
}

export const DashboardPage: React.FC = () => {
  const [isLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateSuccess, setGenerateSuccess] = useState<string | null>(null)
  const [data] = useState<DashboardMetricItem[]>([])
  const [error] = useState<{ code: string; message: string } | null>(null)

  const handleGenerateDemoData = async () => {
    try {
      setIsGenerating(true)
      await apiClient.post('/demo/generate')
      setGenerateSuccess('Demo dataset generated successfully! Invoices, payments, and ledger entries loaded.')
    } catch (err: unknown) {
      console.error('Failed to generate demo data:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const columns: Column<DashboardMetricItem>[] = [
    { key: 'caseNumber', header: 'Case #' },
    { key: 'vendor', header: 'Vendor' },
    {
      key: 'exposure',
      header: 'Exposure',
      align: 'right',
      render: (item) => <MoneyText amount={item.exposure} />,
    },
    {
      key: 'variance',
      header: 'Tax Variance',
      align: 'right',
      render: (item) => <MoneyText amount={item.variance} />,
    },
    {
      key: 'risk',
      header: 'Risk Tier',
      render: (item) => <RiskChip tier={item.risk} />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (item) => <StatusChip status={item.status} />,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Dashboard Overview</h1>
        <p className="text-sm text-slate-500 mt-1">
          Autonomous tax reconciliation metrics and risk intelligence.
        </p>
      </div>

      {/* Metric Cards - Loading / Empty cues, no fake numbers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Financial Exposure"
          value={<MoneyText amount={data.length === 0 ? 0 : null} />}
          subtitle="Awaiting reconciliation"
          icon={<DollarSign className="w-4 h-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Tax Discrepancy Variance"
          value={<MoneyText amount={data.length === 0 ? 0 : null} />}
          subtitle="Statutory risk detected"
          icon={<AlertCircle className="w-4 h-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="Auto-Match Rate"
          value={data.length === 0 ? '—' : '0.0%'}
          subtitle="Deterministic & fuzzy"
          icon={<CheckCircle2 className="w-4 h-4" />}
          isLoading={isLoading}
        />
        <StatCard
          title="High Risk Cases"
          value={data.length === 0 ? '0' : '—'}
          subtitle="SLA escalated items"
          icon={<TrendingUp className="w-4 h-4" />}
          isLoading={isLoading}
        />
      </div>

      {/* Main Table Container */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Priority Tax Discrepancies</h2>
          <span className="text-xs text-slate-400 font-mono">0 items pending</span>
        </div>

        {data.length === 0 && !isLoading && !error ? (
          <EmptyState
            title="No Reconciliation Discrepancies"
            description={
              generateSuccess ||
              "All financial batches are currently balanced or awaiting import. Ingest a new dataset to initiate reconciliation."
            }
            action={{
              label: isGenerating ? 'Generating demo data...' : 'Generate demo data',
              onClick: handleGenerateDemoData,
            }}
          />
        ) : (
          <DataTable
            columns={columns}
            data={data}
            isLoading={isLoading}
            error={error}
            emptyTitle="No Discrepancies Found"
          />
        )}
      </div>
    </div>
  )
}
