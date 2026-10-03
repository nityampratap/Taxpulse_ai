import React, { useState } from 'react'
import { DataTable, type Column, MoneyText, EmptyState } from '../components/shared'
import { UploadCloud, Search } from 'lucide-react'

interface TransactionItem {
  id: string
  referenceId: string
  date: string
  counterparty: string
  amount: number
  source: string
}

export const TransactionsPage: React.FC = () => {
  const [transactions] = useState<TransactionItem[]>([])
  const [isLoading] = useState(false)

  const columns: Column<TransactionItem>[] = [
    { key: 'referenceId', header: 'Reference' },
    { key: 'date', header: 'Date' },
    { key: 'counterparty', header: 'Counterparty' },
    { key: 'source', header: 'Source' },
    {
      key: 'amount',
      header: 'Amount',
      align: 'right',
      render: (item) => <MoneyText amount={item.amount} />,
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

        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm transition-colors"
        >
          <UploadCloud className="w-3.5 h-3.5" />
          Import File (CSV/XLSX)
        </button>
      </div>

      <div className="flex items-center gap-2 max-w-md">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search reference, vendor, or invoice ID..."
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div className="space-y-3">
        {transactions.length === 0 && !isLoading ? (
          <EmptyState
            title="No Ingested Transactions"
            description="No transactions or invoices have been imported into this organization workspace."
            action={{
              label: 'Upload Batch',
              onClick: () => {},
            }}
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
