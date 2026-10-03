# TAXPULSE AI — Design System & UI Specification (DESIGN.md)

## 1. Design Tokens

| Token Category | Token Name | Value | CSS Variable / Tailwind Key | Role / Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Brand / Surface** | Background Page | `#F8FAFC` | `bg-slate-50` | Primary app canvas background |
| | Surface Card | `#FFFFFF` | `bg-white` | Container cards, panels, table backgrounds |
| | Surface Elevated | `#F1F5F9` | `bg-slate-100` | Header rows, table headers, hovered rows |
| | Sidebar Dark | `#0F172A` | `bg-slate-900` | Primary navigation bar background |
| | Sidebar Hover | `#1E293B` | `bg-slate-800` | Navigation item active/hover state |
| **Borders** | Border Subtle | `#E2E8F0` | `border-slate-200` | Card borders, table dividers |
| | Border Strong | `#CBD5E1` | `border-slate-300` | Form inputs, focus boundaries |
| **Typography** | Text Primary | `#0F172A` | `text-slate-900` | Headings, primary metrics, active labels |
| | Text Secondary | `#475569` | `text-slate-600` | Subtitles, descriptions, table body |
| | Text Muted | `#94A3B8` | `text-slate-400` | Placeholders, timestamps, breadcrumbs |
| | Text Inverse | `#FFFFFF` | `text-white` | Button text on dark/brand backgrounds |
| **Brand Primary** | Primary Default | `#2563EB` | `bg-blue-600` | Action buttons, primary links, focus rings |
| | Primary Hover | `#1D4ED8` | `bg-blue-700` | Hovered action buttons |
| | Primary Subtle | `#EFF6FF` | `bg-blue-50` | Active selection pills, highlight backgrounds |
| **Status / Alert** | Success / Reconciled | `#059669` / `#ECFDF5` | `text-emerald-700`, `bg-emerald-50` | Reconciled transactions, clean status |
| *(Status Only)* | Warning / Medium | `#D97706` / `#FFFBEB` | `text-amber-700`, `bg-amber-50` | Warnings, medium risk cases |
| | Danger / High | `#DC2626` / `#FEF2F2` | `text-rose-700`, `bg-rose-50` | Discrepancies, failed runs, high risk |
| | Critical Risk | `#7C3AED` / `#F5F3FF` | `text-purple-700`, `bg-purple-50` | Fraud alert, statutory violation >=75 |
| | Info / Pending | `#2563EB` / `#EFF6FF` | `text-blue-700`, `bg-blue-50` | Pending queue, in review |

---

## 2. Typography & Numerical Formatting

| Hierarchy | Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | 24px (`text-2xl`) | Semibold (600) | 32px | Page titles |
| **Headline** | 18px (`text-lg`) | Semibold (600) | 28px | Card headings, section titles |
| **Body** | 14px (`text-sm`) | Regular (400) | 20px | Table cells, form labels, general body |
| **Caption** | 12px (`text-xs`) | Medium (500) | 16px | Badge labels, table column headers, helper text |
| **Monetary / Code** | 14px (`text-sm`) | Medium (500) | 20px | Tabular numbers (`tabular-nums font-mono`) with INR (₹) or USD format |

---

## 3. Radii, Borders, and Shadows

| Property | Value | Tailwind Class | Usage |
| :--- | :--- | :--- | :--- |
| **Border Radius** | 4px | `rounded` | Chips, badges, small buttons |
| | 6px | `rounded-md` | Form inputs, select dropdowns, buttons |
| | 8px | `rounded-lg` | Stat cards, table containers, modal dialogs |
| **Borders** | 1px solid `#E2E8F0` | `border border-slate-200` | Universal subtle divider on cards & tables |
| **Shadows** | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | `shadow-sm` | Card elevation, clean subtle separation |

---

## 4. Design Do's & Don'ts

| DO | DON'T |
| :--- | :--- |
| **DO**: Use strict `tabular-nums font-mono` for all currency, percentages, and IDs | **NO GRADIENTS**: Strictly use flat, solid backgrounds. |
| **DO**: Reserve red, amber, emerald, and purple ONLY for statutory/risk status | **NO GLASSMORPHISM**: No backdrop blur or semi-transparent floating glass. |
| **DO**: Maintain 1px solid borders for clean, audit-grade enterprise density | **NO DECORATIVE ICONS**: Every icon must serve a direct navigational or state purpose. |
| **DO**: Provide explicit Loading, Empty, and Error states for every view | **NO FAKE NUMBERS**: Empty states should display clean zero/empty cues until APIs load. |

---

## 5. Tailwind Theme Mapping

```javascript
// tailwind.config.js theme extensions
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#EFF6FF',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        surface: {
          canvas: '#F8FAFC',
          card: '#FFFFFF',
          elevated: '#F1F5F9',
        },
        risk: {
          low: { text: '#059669', bg: '#ECFDF5', border: '#A7F3D0' },
          medium: { text: '#D97706', bg: '#FFFBEB', border: '#FDE68A' },
          high: { text: '#DC2626', bg: '#FEF2F2', border: '#FECACA' },
          critical: { text: '#7C3AED', bg: '#F5F3FF', border: '#DDD6FE' },
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      }
    }
  }
}
```

---

## 6. Core Component Standards

| Component | Standard Implementation Rule |
| :--- | :--- |
| **`AppLayout`** | Fixed dark sidebar (`w-64 bg-slate-900`) with 10 nav items, top bar (`h-14 bg-white border-b border-slate-200`) with tenant switcher & user avatar. |
| **`DataTable`** | Compact padding (`py-2.5 px-3`), sticky header, alternating or hovered rows, sorting arrows, pagination controls. |
| **`StatCard`** | 1px border, white background, uppercase title (`text-xs text-slate-500`), large tabular metric (`text-2xl font-semibold`), trend chip. |
| **`StatusChip`** | Rounded-full badge (`px-2.5 py-0.5 text-xs font-medium`) strictly mapped to status colors. |
| **`RiskChip`** | Distinct risk badge for `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` with factor-based semantic styling. |
| **`EmptyState`** | Centered state with outline icon, concise title, descriptive hint, and action button. |
| **`ErrorState`** | Alert container with error code, explanation message, and retry button. |
| **`Skeleton`** | Animated pulse placeholder (`bg-slate-200 rounded animate-pulse`) matching target dimensions. |
| **`MoneyText`** | Formats numbers with tabular numerals (`tabular-nums font-mono`), currency symbol (defaults to INR ₹ or USD $), and Decimal precision. |

---

## 7. Navigation Structure (10 Nav Items)

1. **Dashboard** (`/dashboard`)
2. **Reconciliation** (`/reconciliation`)
3. **Transactions** (`/transactions`)
4. **Exceptions** (`/exceptions`)
5. **Tax Intelligence** (`/tax-intelligence`)
6. **Vendors** (`/vendors`)
7. **Reports** (`/reports`)
8. **WhatsApp Bot** (`/whatsapp`)
9. **Audit Trail** (`/audit`)
10. **Settings** (`/settings`)
