#!/bin/bash
set -e

echo "=== Running Backend Tests ==="
python -m pytest backend/tests/ -v

echo "=== Running Synthetic Evaluation ==="
python backend/scripts/evaluate.py

echo "=== Running Frontend Tests ==="
cd frontend
npm test -- --run
cd ..

echo "=== All Tests Passed Successfully! ==="
