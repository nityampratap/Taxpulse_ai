import React from 'react'
import { cn } from '../../utils/cn'
import { Skeleton } from './Skeleton'
import { EmptyState } from './EmptyState'
import { ErrorState } from './ErrorState'

export interface Column<T> {
  key: string
  header: string | React.ReactNode
  render?: (item: T, index: number) => React.ReactNode
  align?: 'left' | 'center' | 'right'
  className?: string
  width?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data?: T[]
  isLoading?: boolean
  error?: { code: string; message: string; details?: unknown } | null
  onRetry?: () => void
  emptyTitle?: string
  emptyDescription?: string
  rowKey?: (item: T, index: number) => string | number
  onRowClick?: (item: T) => void
  className?: string
}

export function DataTable<T>({
  columns,
  data = [],
  isLoading = false,
  error = null,
  onRetry,
  emptyTitle = 'No data available',
  emptyDescription = 'There are no records to display.',
  rowKey = (_, idx) => idx,
  onRowClick,
  className,
}: DataTableProps<T>) {
  if (error) {
    return (
      <div className="p-4">
        <ErrorState
          code={error.code}
          message={error.message}
          details={error.details}
          onRetry={onRetry}
        />
      </div>
    )
  }

  const safeData = Array.isArray(data) ? data : []

  return (
    <div className={cn('w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm', className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={col.width ? { width: col.width } : undefined}
                  className={cn(
                    'py-2.5 px-3 text-xs font-semibold text-slate-600 uppercase tracking-wider',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.className
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, idx) => (
                <tr key={`skeleton-${idx}`}>
                  {columns.map((col) => (
                    <td key={`sk-${col.key}-${idx}`} className="py-3 px-3">
                      <Skeleton className="h-4 w-full max-w-[120px]" />
                    </td>
                  ))}
                </tr>
              ))
            ) : safeData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-0">
                  <div className="py-12 border-0">
                    <EmptyState
                      title={emptyTitle}
                      description={emptyDescription}
                      className="border-0 shadow-none bg-transparent"
                    />
                  </div>
                </td>
              </tr>
            ) : (
              safeData.map((item, idx) => (
                <tr
                  key={rowKey(item, idx)}
                  onClick={() => onRowClick && onRowClick(item)}
                  className={cn(
                    'transition-colors hover:bg-slate-50/80',
                    onRowClick && 'cursor-pointer'
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'py-2.5 px-3 text-slate-700',
                        col.align === 'right' && 'text-right',
                        col.align === 'center' && 'text-center',
                        col.className
                      )}
                    >
                      {col.render
                        ? col.render(item, idx)
                        : (item as Record<string, unknown>)[col.key] !== undefined
                        ? String((item as Record<string, unknown>)[col.key])
                        : '—'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
