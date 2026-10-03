import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { DataTable, type Column, EmptyState, StatCard, MoneyText } from '../components/shared'
import { Sparkles, ShieldAlert, Percent } from 'lucide-react'
import { apiClient } from '../services/apiClient'

interface TaxRuleItem {
  id: string
  tax_type: string
  jurisdiction: string
  rate: string
  effective_from: string
  effective_to?: string
  is_active: boolean
}

interface TaxSummary {
  total_exposure?: string | number
  variance_count?: number
  disclaimer?: string
}

export const TaxIntelligencePage: React.FC = () => {
  const { data: taxRules = [], isLoading: isRulesLoading } = useQuery<TaxRuleItem[]>({
    queryKey: ['tax', 'rules'],
    queryFn: () => apiClient.get<TaxRuleItem[]>('/tax/rules'),
  })

  const { data: summary, isLoading: isSummaryLoading } = useQuery<TaxSummary>({
    queryKey: ['tax', 'summary'],
    queryFn: () => apiClient.get<TaxSummary>('/tax/summary'),
  })

  const columns: Column<TaxRuleItem>[] = [
    {
      key: 'tax_type',
      header: 'Tax Type',
      render: (item) => (
        <span className="font-semibold text-slate-800">{item.tax_type}</span>
      ),
    },
    { key: 'jurisdiction', header: 'Jurisdiction' },
    {
      key: 'rate',
      header: 'Statutory Rate',
      align: 'right',
      render: (item) => (
        <span className="font-mono font-semibold text-blue-700">
          {(parseFloat(item.rate) * 100).toFixed(2)}%
        </span>
      ),
    },
    { key: 'effective_from', header: 'Effective From' },
    {
      key: 'effective_to',
      header: 'Effective To',
      render: (item) => item.effective_to || 'Active (Indefinite)',
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (item) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
            item.is_active
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-slate-100 text-slate-600'
          }`}
        >
          {item.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  const exposureNum = parseFloat(String(summary?.total_exposure || 0))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tax Intelligence & Rules</h1>
          <p className="text-sm text-slate-500 mt-1">
            Statutory tax rules, jurisdictional rates, and temporal applicability tables.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-500 bg-slate-100 px-3 py-1.5 rounded border border-slate-200">
          Rules Configured: {taxRules.length}
        </div>
      </div>

      {/* Tax Intelligence KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Active Tax Rules"
          value={String(taxRules.length)}
          subtitle="Statutory GST & VAT rates"
          icon={<Percent className="w-4 h-4" />}
          isLoading={isRulesLoading}
        />
        <StatCard
          title="Statutory Tax Variance"
          value={<MoneyText amount={exposureNum} />}
          subtitle="Potential tax exposure"
          icon={<ShieldAlert className="w-4 h-4" />}
          isLoading={isSummaryLoading}
        />
        <StatCard
          title="Flagged Tax Discrepancies"
          value={String(summary?.variance_count ?? 0)}
          subtitle="Awaiting reconciliation review"
          icon={<Sparkles className="w-4 h-4" />}
          isLoading={isSummaryLoading}
        />
      </div>

      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-900">Jurisdictional Tax Table</h2>
        {taxRules.length === 0 && !isRulesLoading ? (
          <EmptyState
            title="No Custom Tax Rules Found"
            description="The engine uses baseline statutory GST/VAT rates. Generate demo data to view the default tax rules."
          />
        ) : (
          <DataTable
            columns={columns}
            data={taxRules}
            isLoading={isRulesLoading}
            emptyTitle="No Tax Rules Configured"
          />
        )}
      </div>

      {summary?.disclaimer && (
        <p className="text-[11px] text-slate-400 italic text-center">
          Notice: {summary.disclaimer}
        </p>
      )}
    </div>
  )
}

export default TaxIntelligencePage

