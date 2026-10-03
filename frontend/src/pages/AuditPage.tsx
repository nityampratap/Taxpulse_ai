import React, { useState } from 'react'
import { DataTable, type Column, EmptyState } from '../components/shared'
import { ShieldCheck } from 'lucide-react'

interface AuditEventItem {
  id: string
  eventType: string
  actorId: string
  entityType: string
  entityId: string
  timestamp: string
  hashChecksum: string
}

export const AuditPage: React.FC = () => {
  const [events] = useState<AuditEventItem[]>([])
  const [isLoading] = useState(false)

  const columns: Column<AuditEventItem>[] = [
    { key: 'timestamp', header: 'Timestamp' },
    { key: 'eventType', header: 'Event Type' },
    { key: 'actorId', header: 'Actor' },
    { key: 'entityType', header: 'Entity' },
    { key: 'entityId', header: 'Target ID' },
    {
      key: 'hashChecksum',
      header: 'SHA-256 Integrity Hash',
      render: (item) => (
        <span className="font-mono text-xs text-slate-500 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
          {item.hashChecksum ? `${item.hashChecksum.substring(0, 16)}...` : '—'}
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
          Append-Only Log
        </div>
      </div>

      <div className="space-y-3">
        {events.length === 0 && !isLoading ? (
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
