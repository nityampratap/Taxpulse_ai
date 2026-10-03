import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DataTable, type Column, MoneyText, StatusChip, RiskChip, EmptyState } from '../components/shared'
import { Filter } from 'lucide-react'

interface ExceptionItem {
  id: string
  caseNumber: string
  vendor: string
  taxImpact: number
  exposure: number
  riskScore: number
  status: string
}

export const ExceptionsPage: React.FC = () => {
  const navigate = useNavigate()
  const [exceptions] = useState<ExceptionItem[]>([])
  const [isLoading] = useState(false)

  const columns: Column<ExceptionItem>[] = [
    { key: 'caseNumber', header: 'Case #' },
    { key: 'vendor', header: 'Vendor' },
    {
      key: 'taxImpact',
      header: 'Tax Impact',
      align: 'right',
      render: (item) => <MoneyText amount={item.taxImpact} />,
    },
    {
      key: 'exposure',
      header: 'Gross Exposure',
      align: 'right',
      render: (item) => <MoneyText amount={item.exposure} />,
    },
    {
      key: 'riskScore',
      header: 'Risk Score',
      render: (item) => <RiskChip score={item.riskScore} />,
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
        {exceptions.length === 0 && !isLoading ? (
          <EmptyState
            title="No Active Discrepancies"
            description="Zero tax variances or unmatched exception cases detected in the active ledger."
          />
        ) : (
          <DataTable
            columns={columns}
            data={exceptions}
            isLoading={isLoading}
            onRowClick={(item) => navigate(`/exceptions/${item.id}`)}
            emptyTitle="No Exceptions Detected"
          />
        )}
      </div>
    </div>
  )
}
