import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { DataTable, type Column, MoneyText, EmptyState } from '../components/shared'
import { apiClient } from '../services/apiClient'

interface TransactionItem {
  id: string
  reference_id: string
  source: string
  transaction_date: string
  amount: string
  currency: string
  description?: string
  counterparty_name?: string
}

export const TransactionsPage: React.FC = () => {
  const { data, isLoading, error } = useQuery<{ transactions: TransactionItem[]; total: number }>({
    queryKey: ['transactions'],
    queryFn: () => apiClient.get<{ transactions: TransactionItem[]; total: number }>('/transactions'),
  })

  const transactions = data?.transactions || []

  const columns: Column<TransactionItem>[] = [
    {
      key: 'reference_id',
      header: 'Reference',
      render: (item) => <span className="font-mono text-xs font-semibold text-slate-800">{item.reference_id}</span>,
    },
    { key: 'transaction_date', header: 'Date' },
    {
      key: 'counterparty_name',
      header: 'Counterparty',
      render: (item) => item.counterparty_name || item.description || '—',
    },
    {
      key: 'source',
      header: 'Source',
      render: (item) => (
        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
          {item.source}
        </span>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      align: 'right',
      render: (item) => <MoneyText amount={parseFloat(item.amount)} />,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Transactions & Invoices</h1>
          <p className="text-sm text-slate-500 mt-1">
            Raw ingested bank feeds, ERP invoices, and payment records.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-500 bg-slate-100 px-3 py-1.5 rounded border border-slate-200">
          Total Ingested: {data?.total ?? transactions.length}
        </div>
      </div>

      <div className="space-y-3">
        {transactions.length === 0 && !isLoading && !error ? (
          <EmptyState
            title="No Ingested Transactions"
            description="No transactions or invoices have been imported. Generate demo data on the Dashboard to load 100+ transactions."
          />
        ) : (
          <DataTable
            columns={columns}
            data={transactions}
            isLoading={isLoading}
            emptyTitle="No Transactions Found"
          />
        )}
      </div>
    </div>
  )
}

export default TransactionsPage

