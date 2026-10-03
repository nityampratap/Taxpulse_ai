import React from 'react'
import { cn } from '../../utils/cn'

interface MoneyTextProps {
  amount?: number | string | null
  currency?: string
  className?: string
  decimals?: number
}

export const MoneyText: React.FC<MoneyTextProps> = ({
  amount,
  currency = 'INR',
  className,
  decimals = 2,
}) => {
  if (amount === null || amount === undefined || amount === '') {
    return <span className={cn('tabular-nums font-mono text-slate-400', className)}>—</span>
  }

  const numericValue = typeof amount === 'number' ? amount : parseFloat(amount)

  if (isNaN(numericValue)) {
    return <span className={cn('tabular-nums font-mono text-slate-400', className)}>—</span>
  }

  const formatted = new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(numericValue)

  return (
    <span className={cn('tabular-nums font-mono font-medium', className)}>
      {formatted}
    </span>
  )
}
