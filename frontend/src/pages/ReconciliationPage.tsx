import React, { useState } from 'react'
import { DataTable, type Column, StatusChip, EmptyState } from '../components/shared'
import { Play, Filter } from 'lucide-react'

interface ReconciliationRun {
  id: string
  timestamp: string
  totalRecords: number
  matchedCount: number
  varianceCount: number
  status: string
}

export const ReconciliationPage: React.FC = () => {
  const [runs] = useState<ReconciliationRun[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleRunReconciliation = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 800)
  }

  const columns: Column<ReconciliationRun>[] = [
    { key: 'id', header: 'Run ID' },
    { key: 'timestamp', header: 'Timestamp' },
    { key: 'totalRecords', header: 'Processed', align: 'right' },
    { key: 'matchedCount', header: 'Matched', align: 'right' },
    { key: 'varianceCount', header: 'Variances', align: 'right' },
    {
      key: 'status',
      header: 'Status',
      render: (item) => <StatusChip status={item.status} />,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Reconciliation Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic, fuzzy, semantic, and split-line reconciliation runs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 shadow-sm"
          >
            <Filter className="w-3.5 h-3.5" />
            Filter Runs
          </button>
          <button
            type="button"
            onClick={handleRunReconciliation}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isLoading ? 'Processing Pipeline...' : 'Run Reconciliation'}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-900">Execution History</h2>
        {runs.length === 0 && !isLoading ? (
          <EmptyState
            title="No Reconciliation Runs"
            description="No batch matching runs have been executed for this organization yet. Click 'Run Reconciliation' to match imported transactions."
            action={{
              label: 'Trigger Run',
              onClick: handleRunReconciliation,
            }}
          />
        ) : (
          <DataTable
            columns={columns}
            data={runs}
            isLoading={isLoading}
            emptyTitle="No Runs Executed"
          />
        )}
      </div>
    </div>
  )
}
