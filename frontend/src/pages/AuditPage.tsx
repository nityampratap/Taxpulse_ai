import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { DataTable, type Column, EmptyState } from '../components/shared'
import { ShieldCheck } from 'lucide-react'
import { apiClient } from '../services/apiClient'

interface AuditEventItem {
  id: string
  event_type: string
  actor_id: string
  entity_type: string
  entity_id: string
  timestamp: string
  hash_checksum: string
  after_state?: Record<string, unknown>
}

export const AuditPage: React.FC = () => {
  const { data: events = [], isLoading, error } = useQuery<AuditEventItem[]>({
    queryKey: ['audit', 'events'],
    queryFn: () => apiClient.get<AuditEventItem[]>('/audit/events'),
  })

  const columns: Column<AuditEventItem>[] = [
    {
      key: 'timestamp',
      header: 'Timestamp',
      render: (item) => (
        <span className="font-mono text-xs text-slate-600">
          {item.timestamp ? item.timestamp.split('.')[0] : '—'}
        </span>
      ),
    },
    {
      key: 'event_type',
      header: 'Event Type',
      render: (item) => (
        <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
          {item.event_type}
        </span>
      ),
    },
    {
      key: 'actor_id',
      header: 'Actor',
      render: (item) => (
        <span className="font-mono text-xs text-slate-600">
          {item.actor_id.length > 12 ? `${item.actor_id.substring(0, 8)}...` : item.actor_id}
        </span>
      ),
    },
    { key: 'entity_type', header: 'Entity' },
    {
      key: 'entity_id',
      header: 'Target ID',
      render: (item) => (
        <span className="font-mono text-xs text-slate-500">
          {item.entity_id.length > 12 ? `${item.entity_id.substring(0, 8)}...` : item.entity_id}
        </span>
      ),
    },
    {
      key: 'hash_checksum',
      header: 'SHA-256 Integrity Hash',
      render: (item) => (
        <span className="font-mono text-xs text-slate-500 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
          {item.hash_checksum ? `${item.hash_checksum.substring(0, 16)}...` : '—'}
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Compliance Audit Trail</h1>
          <p className="text-sm text-slate-500 mt-1">
            Immutable, append-only event stream with cryptographic checksums.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1 bg-slate-100 rounded-md border border-slate-200 text-xs font-mono text-slate-600">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
          Append-Only Log ({events.length} events)
        </div>
      </div>

      <div className="space-y-3">
        {events.length === 0 && !isLoading && !error ? (
          <EmptyState
            title="No Audit Events Recorded"
            description="All platform operations, state transitions, and reconciliation runs will generate immutable records here."
          />
        ) : (
          <DataTable
            columns={columns}
            data={events}
            isLoading={isLoading}
            emptyTitle="No Audit Logs"
          />
        )}
      </div>
    </div>
  )
}

export default AuditPage

