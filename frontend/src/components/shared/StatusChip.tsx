import React from 'react'
import { cn } from '../../utils/cn'

export type StatusType =
  | 'RECONCILED'
  | 'MATCHED'
  | 'SUCCESS'
  | 'COMPLETED'
  | 'ACTIVE'
  | 'PENDING'
  | 'IN_REVIEW'
  | 'IN_PROGRESS'
  | 'PARSED'
  | 'WARNING'
  | 'VARIANCE'
  | 'DISPUTED'
  | 'FAILED'
  | 'ERROR'
  | 'REJECTED'
  | 'OPEN'

interface StatusChipProps {
  status: string
  label?: string
  className?: string
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, label, className }) => {
  const normalized = status.toUpperCase().trim()
  const displayLabel = label || status.replace(/_/g, ' ')

  let style = 'bg-slate-100 text-slate-700 border-slate-200'

  if (['RECONCILED', 'MATCHED', 'SUCCESS', 'COMPLETED', 'ACTIVE'].includes(normalized)) {
    style = 'bg-emerald-50 text-emerald-700 border-emerald-200'
  } else if (['PENDING', 'IN_REVIEW', 'IN_PROGRESS', 'PARSED', 'OPEN'].includes(normalized)) {
    style = 'bg-blue-50 text-blue-700 border-blue-200'
  } else if (['WARNING', 'VARIANCE', 'DISPUTED'].includes(normalized)) {
    style = 'bg-amber-50 text-amber-700 border-amber-200'
  } else if (['FAILED', 'ERROR', 'REJECTED'].includes(normalized)) {
    style = 'bg-rose-50 text-rose-700 border-rose-200'
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border uppercase tracking-wider',
        style,
        className
      )}
    >
      {displayLabel}
    </span>
  )
}
