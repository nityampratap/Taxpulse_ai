import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { DataTable, type Column, StatusChip, EmptyState } from '../components/shared'
import { Play } from 'lucide-react'
import { apiClient } from '../services/apiClient'

interface ReconciliationRun {
  id: string
  run_timestamp: string
  total_processed: number
  matched_count: number
  variance_count: number
  status: string
  batch_id?: string
}

export const ReconciliationPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [isRunning, setIsRunning] = useState(false)
  const [runMessage, setRunMessage] = useState<string | null>(null)

  const { data: runs = [], isLoading } = useQuery<ReconciliationRun[]>({
    queryKey: ['reconciliation', 'runs'],
    queryFn: () => apiClient.get<ReconciliationRun[]>('/reconciliation/runs'),
  })

  const handleRunReconciliation = async () => {
    try {
      setIsRunning(true)
      const res = await apiClient.post<{
        run_id: string
        total_processed: number
        matched_count: number
        variance_count: number
        cases_created: number
      }>('/reconciliation/run', {})
      setRunMessage(
        `Run completed! Processed ${res.total_processed} records: ${res.matched_count} matched, ${res.variance_count} variances (${res.cases_created} cases created).`
      )
      await queryClient.invalidateQueries({ queryKey: ['reconciliation'] })
      await queryClient.invalidateQueries({ queryKey: ['cases'] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    } catch (err) {
      console.error('Failed to run reconciliation:', err)
    } finally {
      setIsRunning(false)
    }
  }

  const columns: Column<ReconciliationRun>[] = [
    {
      key: 'id',
      header: 'Run ID',
      render: (item) => (
        <span className="font-mono text-xs text-slate-700">
          {item.id.length > 12 ? `${item.id.substring(0, 8)}...` : item.id}
        </span>
      ),
    },
    {
      key: 'run_timestamp',
      header: 'Timestamp',
      render: (item) => (
        <span className="font-mono text-xs text-slate-600">
          {item.run_timestamp ? item.run_timestamp.split('.')[0] : '—'}
        </span>
      ),
    },
    {
      key: 'total_processed',
      header: 'Processed',
      align: 'right',
      render: (item) => <span className="font-mono">{item.total_processed}</span>,
    },
    {
      key: 'matched_count',
      header: 'Matched',
      align: 'right',
      render: (item) => (
        <span className="font-mono text-emerald-600 font-semibold">{item.matched_count}</span>
      ),
    },
    {
      key: 'variance_count',
      header: 'Variances',
      align: 'right',
      render: (item) => (
        <span className="font-mono text-amber-600 font-semibold">{item.variance_count}</span>
      ),
    },
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
            onClick={handleRunReconciliation}
            disabled={isRunning}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isRunning ? 'Processing Pipeline...' : 'Run Reconciliation'}
          </button>
        </div>
      </div>

      {runMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-md font-medium">
          {runMessage}
        </div>
      )}

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

export default ReconciliationPage

