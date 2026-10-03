import '@testing-library/jest-dom/vitest'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppRoutes } from '../App'

function renderWithRoute(route: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Route Smoke Tests', () => {
  it('renders /login route', () => {
    renderWithRoute('/login')
    expect(screen.getByText('TAXPULSE AI')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In to Workspace/i })).toBeInTheDocument()
  })

  it('renders /dashboard route', () => {
    renderWithRoute('/dashboard')
    expect(screen.getByRole('heading', { level: 1, name: 'Dashboard Overview' })).toBeInTheDocument()
  })

  it('renders /reconciliation route', () => {
    renderWithRoute('/reconciliation')
    expect(screen.getByRole('heading', { level: 1, name: 'Reconciliation Engine' })).toBeInTheDocument()
  })

  it('renders /transactions route', () => {
    renderWithRoute('/transactions')
    expect(screen.getByRole('heading', { level: 1, name: 'Transactions & Invoices' })).toBeInTheDocument()
  })

  it('renders /exceptions route', () => {
    renderWithRoute('/exceptions')
    expect(screen.getByRole('heading', { level: 1, name: 'Tax Exceptions & Discrepancies' })).toBeInTheDocument()
  })

  it('renders /exceptions/:id route', () => {
    renderWithRoute('/exceptions/TX-10482')
    expect(screen.getByRole('heading', { level: 1, name: 'Case TX-10482' })).toBeInTheDocument()
  })

  it('renders /tax-intelligence route', () => {
    renderWithRoute('/tax-intelligence')
    expect(screen.getByRole('heading', { level: 1, name: 'Tax Intelligence & Rules' })).toBeInTheDocument()
  })

  it('renders /vendors route', () => {
    renderWithRoute('/vendors')
    expect(screen.getByRole('heading', { level: 1, name: 'Vendor Directory' })).toBeInTheDocument()
  })

  it('renders /reports route', () => {
    renderWithRoute('/reports')
    expect(screen.getByRole('heading', { level: 1, name: 'Compliance Reports' })).toBeInTheDocument()
  })

  it('renders /whatsapp route', () => {
    renderWithRoute('/whatsapp')
    expect(screen.getByRole('heading', { level: 1, name: 'WhatsApp Review Channel' })).toBeInTheDocument()
  })

  it('renders /audit route', () => {
    renderWithRoute('/audit')
    expect(screen.getByRole('heading', { level: 1, name: 'Compliance Audit Trail' })).toBeInTheDocument()
  })

  it('renders /settings route', () => {
    renderWithRoute('/settings')
    expect(screen.getByRole('heading', { level: 1, name: 'Organization Settings' })).toBeInTheDocument()
  })
})
