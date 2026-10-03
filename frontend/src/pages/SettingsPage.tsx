import React from 'react'

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Organization Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Tenancy configuration, matching tolerances, and AI provider parameters.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* General Tenancy */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-slate-900">Organization Profile</h2>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Organization Name
            </label>
            <input
              type="text"
              defaultValue="TaxPulse Global Enterprises"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-md"
              readOnly
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Default Jurisdiction
            </label>
            <input
              type="text"
              defaultValue="IN-MH (GST 18%)"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-md"
              readOnly
            />
          </div>
        </div>

        {/* Engine Parameters */}
        <div className="p-5 bg-white rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-semibold text-slate-900">Reconciliation Parameters</h2>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Penny Tolerance Boundary (INR ₹ / USD $)
            </label>
            <input
              type="number"
              defaultValue="0.05"
              step="0.01"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-md font-mono"
              readOnly
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Fuzzy Matching Threshold (RapidFuzz)
            </label>
            <input
              type="text"
              defaultValue="0.85 (85% Token Ratio)"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-300 rounded-md font-mono"
              readOnly
            />
          </div>
        </div>
      </div>
    </div>
  )
}
