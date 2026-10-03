import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DataTable, type Column, RiskChip, EmptyState } from '../components/shared'
import { Search } from 'lucide-react'
import { apiClient } from '../services/apiClient'

interface VendorItem {
  id: string
  name: string
  normalized_name: string
  tax_identifier: string
  risk_tier: string
  dispute_count: number
}

export const VendorsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')

  const { data: vendors = [], isLoading, error } = useQuery<VendorItem[]>({
    queryKey: ['vendors'],
    queryFn: () => apiClient.get<VendorItem[]>('/vendors'),
  })

  const filteredVendors = vendors.filter(
    (v) =>
      v.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.tax_identifier?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      v.normalized_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const columns: Column<VendorItem>[] = [
    { key: 'name', header: 'Vendor Name' },
    { key: 'normalized_name', header: 'Normalized Alias' },
    { key: 'tax_identifier', header: 'GSTIN / Tax ID' },
    {
      key: 'risk_tier',
      header: 'Vendor Risk',
      render: (item) => <RiskChip tier={item.risk_tier} />,
    },
    {
      key: 'dispute_count',
      header: 'Disputes',
      align: 'right',
      render: (item) => <span className="tabular-nums font-mono font-medium">{item.dispute_count}</span>,
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

        <div className="text-xs font-mono text-slate-500 bg-slate-100 px-3 py-1.5 rounded border border-slate-200">
          Indexed Vendors: {vendors.length}
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by vendor name or tax identifier..."
          className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div className="space-y-3">
        {filteredVendors.length === 0 && !isLoading && !error ? (
          <EmptyState
            title="No Vendors Found"
            description={
              searchTerm
                ? `No vendor matches for "${searchTerm}".`
                : 'Vendors will automatically be extracted and indexed upon generating demo data.'
            }
          />
        ) : (
          <DataTable
            columns={columns}
            data={filteredVendors}
            isLoading={isLoading}
            emptyTitle="No Vendors Available"
          />
        )}
      </div>
    </div>
  )
}

export default VendorsPage

