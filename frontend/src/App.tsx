import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from './components/layout/AppLayout'
import {
  LoginPage,
  DashboardPage,
  ReconciliationPage,
  TransactionsPage,
  ExceptionsPage,
  ExceptionDetailPage,
  TaxIntelligencePage,
  VendorsPage,
  ReportsPage,
  WhatsAppPage,
  AuditPage,
  SettingsPage,
} from './pages'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<AppLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/reconciliation" element={<ReconciliationPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/exceptions" element={<ExceptionsPage />} />
        <Route path="/exceptions/:id" element={<ExceptionDetailPage />} />
        <Route path="/tax-intelligence" element={<TaxIntelligencePage />} />
        <Route path="/vendors" element={<VendorsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/whatsapp" element={<WhatsAppPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
