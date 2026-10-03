import React, { useState } from 'react'
import { DataTable, type Column, RiskChip, EmptyState } from '../components/shared'
import { Search } from 'lucide-react'

interface VendorItem {
  id: string
  name: string
  normalizedName: string
  taxIdentifier: string
  riskTier: string
  disputeCount: number
}

export const VendorsPage: React.FC = () => {
  const [vendors] = useState<VendorItem[]>([])
  const [isLoading] = useState(false)

  const columns: Column<VendorItem>[] = [
    { key: 'name', header: 'Vendor Name' },
    { key: 'normalizedName', header: 'Normalized Alias' },
    { key: 'taxIdentifier', header: 'GSTIN / Tax ID' },
    {
      key: 'riskTier',
      header: 'Vendor Risk',
      render: (item) => <RiskChip tier={item.riskTier} />,
    },
    {
      key: 'disputeCount',
      header: 'Disputes',
      align: 'right',
      render: (item) => <span className="tabular-nums font-mono">{item.disputeCount}</span>,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Vendor Directory</h1>
          <p className="text-sm text-slate-500 mt-1">
            Vendor profiles, normalized fuzzy matching dictionaries, and dispute track records.
          </p>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        <input
          type="text"
          placeholder="Search by vendor name or tax identifier..."
          className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div className="space-y-3">
        {vendors.length === 0 && !isLoading ? (
          <EmptyState
            title="No Vendors Registered"
            description="Vendors will automatically be extracted and indexed upon file ingestion."
          />
        ) : (
          <DataTable
            columns={columns}
            data={vendors}
            isLoading={isLoading}
            emptyTitle="No Vendors Available"
          />
        )}
      </div>
    </div>
  )
}
