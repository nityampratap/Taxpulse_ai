import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '../../utils/cn'

interface ErrorStateProps {
  code?: string
  message?: string
  details?: unknown
  onRetry?: () => void
  className?: string
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  code = 'LOAD_FAILED',
  message = 'An error occurred while loading this data.',
  details,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-6 bg-rose-50 border border-rose-200 rounded-lg text-slate-800',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-600 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-rose-900">Request Error</h4>
            <span className="font-mono text-xs text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded border border-rose-300">
              {code}
            </span>
          </div>
          <p className="text-sm text-rose-700 mb-3">{message}</p>

          {details !== undefined && (
            <pre className="text-xs bg-white/70 p-2 rounded border border-rose-200 overflow-x-auto text-slate-700 font-mono mb-3">
              {typeof details === 'string' ? details : JSON.stringify(details, null, 2)}
            </pre>
          )}

          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-1"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Request
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
