import React from 'react'
import { cn } from '../../utils/cn'

export type RiskTier = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

interface RiskChipProps {
  tier?: string
  score?: number | string
  className?: string
}

export const RiskChip: React.FC<RiskChipProps> = ({ tier, score, className }) => {
  let resolvedTier: RiskTier = 'LOW'

  if (tier) {
    resolvedTier = tier.toUpperCase() as RiskTier
  } else if (score !== undefined && score !== null) {
    const num = typeof score === 'number' ? score : parseFloat(score)
    if (num >= 75) resolvedTier = 'CRITICAL'
    else if (num >= 55) resolvedTier = 'HIGH'
    else if (num >= 30) resolvedTier = 'MEDIUM'
    else resolvedTier = 'LOW'
  }

  const styles: Record<RiskTier, string> = {
    LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200',
    HIGH: 'bg-rose-50 text-rose-700 border-rose-200',
    CRITICAL: 'bg-purple-50 text-purple-700 border-purple-200',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold border tracking-wide uppercase',
        styles[resolvedTier] || styles.LOW,
        className
      )}
    >
      <span
        className={cn('w-1.5 h-1.5 rounded-full', {
          'bg-emerald-600': resolvedTier === 'LOW',
          'bg-amber-600': resolvedTier === 'MEDIUM',
          'bg-rose-600': resolvedTier === 'HIGH',
          'bg-purple-600': resolvedTier === 'CRITICAL',
        })}
      />
      {resolvedTier}
      {score !== undefined && (
        <span className="font-mono tabular-nums opacity-80">({score})</span>
      )}
    </span>
  )
}
