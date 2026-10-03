import React from 'react'
import { cn } from '../../utils/cn'
import { Skeleton } from './Skeleton'

interface StatCardProps {
  title: string
  value?: React.ReactNode
  subtitle?: string
  trend?: {
    value: string
    isPositive?: boolean
    neutral?: boolean
  }
  icon?: React.ReactNode
  isLoading?: boolean
  className?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  isLoading = false,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-5 bg-white rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between',
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        {icon && <span className="text-slate-400">{icon}</span>}
      </div>

      <div className="my-1">
        {isLoading ? (
          <Skeleton className="h-8 w-28 my-1" />
        ) : (
          <div className="text-2xl font-semibold text-slate-900 tabular-nums font-mono tracking-tight">
            {value ?? '—'}
          </div>
        )}
      </div>

      {(subtitle || trend) && (
        <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
          {trend && (
            <span
              className={cn(
                'font-medium px-1.5 py-0.5 rounded text-[11px]',
                trend.neutral
                  ? 'bg-slate-100 text-slate-600'
                  : trend.isPositive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-rose-50 text-rose-700'
              )}
            >
              {trend.value}
            </span>
          )}
          {subtitle && <span>{subtitle}</span>}
        </div>
      )}
    </div>
  )
}
