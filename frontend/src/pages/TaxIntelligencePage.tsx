import React, { useState } from 'react'
import { DataTable, type Column, EmptyState } from '../components/shared'
import { Plus } from 'lucide-react'

interface TaxRuleItem {
  id: string
  taxType: string
  jurisdiction: string
  rate: number
  effectiveFrom: string
  effectiveTo?: string
  status: string
}

export const TaxIntelligencePage: React.FC = () => {
  const [taxRules] = useState<TaxRuleItem[]>([])
  const [isLoading] = useState(false)

  const columns: Column<TaxRuleItem>[] = [
    { key: 'taxType', header: 'Tax Type' },
    { key: 'jurisdiction', header: 'Jurisdiction' },
    {
      key: 'rate',
      header: 'Statutory Rate',
      align: 'right',
      render: (item) => `${(item.rate * 100).toFixed(2)}%`,
    },
    { key: 'effectiveFrom', header: 'Effective From' },
    {
      key: 'effectiveTo',
      header: 'Effective To',
      render: (item) => item.effectiveTo || 'Active (Indefinite)',
    },
    { key: 'status', header: 'Status' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tax Intelligence & Rules</h1>
          <p className="text-sm text-slate-500 mt-1">
            Statutory tax rules, jurisdictional rates, and temporal applicability tables.
          </p>
        </div>

        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Tax Rule
        </button>
      </div>

      <div className="space-y-3">
        {taxRules.length === 0 && !isLoading ? (
          <EmptyState
            title="No Custom Tax Rules Found"
            description="The engine is currently utilizing baseline statutory GST/VAT rates. Add jurisdictional rules to customize tax calculation tolerances."
            action={{
              label: 'Add First Rule',
              onClick: () => {},
            }}
          />
        ) : (
          <DataTable
            columns={columns}
            data={taxRules}
            isLoading={isLoading}
            emptyTitle="No Tax Rules Configured"
          />
        )}
      </div>
    </div>
  )
}
