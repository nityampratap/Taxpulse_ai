import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { DataTable, type Column, MoneyText, StatusChip, RiskChip, EmptyState } from '../components/shared'
import { apiClient } from '../services/apiClient'
import { Filter } from 'lucide-react'

interface CaseItem {
  id: string
  case_number: string
  vendor?: string
  tax_impact: string
  financial_exposure: string
  risk_score: string
  priority: string
  status: string
}

export const ExceptionsPage: React.FC = () => {
  const navigate = useNavigate()

  const { data: casesData, isLoading, error } = useQuery<{ cases: CaseItem[] } | CaseItem[]>({
    queryKey: ['cases'],
    queryFn: () => apiClient.get<{ cases: CaseItem[] } | CaseItem[]>('/cases'),
  })

  const exceptions: CaseItem[] = Array.isArray(casesData)
    ? casesData
    : (casesData as unknown as { cases?: CaseItem[] })?.cases || []

  const columns: Column<CaseItem>[] = [
    {
      key: 'case_number',
      header: 'Case #',
      render: (item) => (
        <span className="font-mono font-medium text-emerald-700 hover:underline">
          {item.case_number}
        </span>
      ),
    },
    { key: 'vendor', header: 'Vendor', render: (item) => item.vendor || '—' },
    {
      key: 'tax_impact',
      header: 'Tax Impact',
      align: 'right',
      render: (item) => <MoneyText amount={parseFloat(item.tax_impact)} />,
    },
    {
      key: 'financial_exposure',
      header: 'Gross Exposure',
      align: 'right',
      render: (item) => <MoneyText amount={parseFloat(item.financial_exposure)} />,
    },
    {
      key: 'priority',
      header: 'Risk Score',
      render: (item) => <RiskChip tier={item.priority} score={parseFloat(item.risk_score)} />,
    },
    {
      key: 'status',
      header: 'Case Status',
      render: (item) => <StatusChip status={item.status} />,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tax Exceptions & Discrepancies</h1>
          <p className="text-sm text-slate-500 mt-1">
            Cases flagged by rule engine, fuzzy matcher, and ML anomaly detector.
          </p>
        </div>

        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 shadow-sm"
        >
          <Filter className="w-3.5 h-3.5" />
          Filter by Risk
        </button>
      </div>

      <div className="space-y-3">
        {exceptions.length === 0 && !isLoading && !error ? (
          <EmptyState
            title="No Active Discrepancies"
            description="Zero tax variances or unmatched exception cases detected in the active ledger."
          />
        ) : (
          <DataTable
            columns={columns}
            data={exceptions}
            isLoading={isLoading}
            error={error ? { code: 'QUERY_ERROR', message: String(error) } : null}
            onRowClick={(item) => navigate(`/exceptions/${item.case_number}`)}
            emptyTitle="No Exceptions Detected"
          />
        )}
      </div>
    </div>
  )
}

export default ExceptionsPage
