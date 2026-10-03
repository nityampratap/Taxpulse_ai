# Agent Guidelines & Project Standards

## Tech Stack
- **Frontend**: React + Vite + TypeScript + Tailwind CSS + TanStack Query
- **Backend**: FastAPI + SQLAlchemy + Pandas + RapidFuzz + scikit-learn
- **Database**: PostgreSQL (with SQLite fallback for local development)

## Rules & Principles
1. **Small Diffs**: Keep changes focused, incremental, and minimal.
2. **Preserve Code**: Never rewrite or modify unrelated code.
3. **Testing**: Run tests after every change to verify correctness.
4. **Changelog**: Keep CHANGELOG.md updated with significant updates.
5. **Decisions**: Record architectural and design decisions in docs/DECISIONS.md.
6. **Secrets & Security**: Never commit or expose secrets in frontend code or git.
   - Frontend: Safe to expose anon/publishable keys only.
   - Backend: Keep service_role/secret keys restricted to backend server code.
7. **Monetary Values**: Always use Decimal for currency/money calculations.
