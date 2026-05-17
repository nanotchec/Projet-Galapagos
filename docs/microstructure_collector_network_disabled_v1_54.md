# Microstructure Collector (Network-Disabled) - V1.54

## Overview
This version implements the initial architecture for the microstructure data collector. As per the `INFRASTRUCTURE_ONLY` constraint, all network features are explicitly disabled and guarded.

## Components

### 1. Configuration (`config_schema.py`)
Uses Pydantic to enforce strict configuration types, including a mandatory `network_disabled=True` flag.

### 2. Network Guard (`network_guard.py`)
A safety mechanism that monkey-patches the `socket` module to raise `NetworkDisabledError` if any attempt to open a socket is made.

### 3. Source Adapters (`binance_adapter_stub.py`, `bybit_adapter_stub.py`)
Stub implementations that demonstrate how requests are built for different exchanges without actually executing them.

### 4. Dry-Run Executor (`dry_run_executor.py`)
Simulates the collection workflow and logs planned actions, ensuring no real execution occurs.

### 5. Validation (`manifest_validator.py`, `file_layout_validator.py`)
Ensures that theoretical data structures and storage paths conform to the project standards.

## Safety Controls
- **Network Block**: Verified by unit tests that raw socket calls are intercepted.
- **Dry-Run Enforced**: The executor refuses to run if `dry_run_only` is False.
- **Audit Reports**: Every execution generates a safety audit report confirming all constraints were met.

## Next Steps
The next phase (V1.55) will focus on implementing local fixture tests to verify the data processing pipeline before considering any real network-enabled collection.
