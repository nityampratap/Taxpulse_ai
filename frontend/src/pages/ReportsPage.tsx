import React, { useState } from 'react'
import { DataTable, type Column, EmptyState } from '../components/shared'
import { Download } from 'lucide-react'

interface ReportItem {
  id: string
  period: string
  generatedAt: string
  totalMatched: number
  totalVariance: number
  status: string
}

export const ReportsPage: React.FC = () => {
  const [reports] = useState<ReportItem[]>([])
  const [isLoading] = useState(false)

  const columns: Column<ReportItem>[] = [
    { key: 'period', header: 'Filing Period' },
    { key: 'generatedAt', header: 'Generated At' },
    { key: 'totalMatched', header: 'Matched Records', align: 'right' },
    { key: 'totalVariance', header: 'Net Variance', align: 'right' },
    { key: 'status', header: 'Status' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Compliance Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Reconciliation statements, tax liability summaries, and audit export packages.
          </p>
        </div>

        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Export Statement (CSV/XLSX)
        </button>
      </div>

      <div className="space-y-3">
        {reports.length === 0 && !isLoading ? (
          <EmptyState
            title="No Statements Generated"
            description="Run a reconciliation cycle to generate period audit statements and tax liability filings."
          />
        ) : (
          <DataTable
            columns={columns}
            data={reports}
            isLoading={isLoading}
            emptyTitle="No Reports Available"
          />
        )}
      </div>
    </div>
  )
}
