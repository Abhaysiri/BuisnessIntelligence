# Builder script for R1 Architectural Plan
import os

target = r'.agents/worker_m1/r1_plan.md'

with open(target, 'w', encoding='utf-8') as f:
    f.write('# Architectural Specification & Technical Implementation Plan\n')
    f.write('## Requirement R1: Data Ingestion & Validity Layer\n\n')
    f.write('- **Author**: Worker 1 (Data Ingestion & Validity Layer Architect)\n')
    f.write('- **Role**: Data Infrastructure & Integrity Architect\n')
    f.write('- **Milestone**: M1 (Data Ingestion & Validity Layer Plan)\n')
    f.write('- **Status**: Complete / Authoritative\n')
    f.write('- **Target File**: .agents/worker_m1/r1_plan.md\n')
    f.write('- **Dependencies**: None (Foundational Layer)\n\n')
    f.write('---\n\n')

print('Step 1 complete')
