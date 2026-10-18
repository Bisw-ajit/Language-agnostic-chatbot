#!/usr/bin/env python3
"""
Odisha Government Incremental Corpus Ingestion CLI
Command Model:
  python ingest.py "PROCESS PRIORITY 1"
  python ingest.py "PROCESS PRIORITY 2"
  python ingest.py "PROCESS AGRICULTURE"
"""

import sys
import os

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.rag.odisha_corpus_manager import (
    resolve_department_command,
    OdishaCorpusIngestionEngine,
    PRIORITY_REGISTRY
)

def print_help():
    print("\n==================================================")
    print("ODISHA GOVERNMENT INCREMENTAL INGESTION SYSTEM")
    print("==================================================")
    print("Usage:")
    print("  python ingest.py \"PROCESS PRIORITY 1\"")
    print("  python ingest.py \"PROCESS PRIORITY 2\"")
    print("  python ingest.py \"PROCESS AGRICULTURE\"")
    print("\nAvailable Priority Departments:")
    for p_key, info in PRIORITY_REGISTRY.items():
        print(f"  {p_key:3s} -> {info['name']}")
    print("==================================================\n")

def main():
    if len(sys.argv) < 2:
        print("Error: Missing department command.")
        print_help()
        sys.exit(1)

    command_str = " ".join(sys.argv[1:])
    if command_str.strip().lower() in ["--help", "-h", "help"]:
        print_help()
        sys.exit(0)

    dept_config = resolve_department_command(command_str)
    if not dept_config:
        print(f"\nError: Could not resolve department from command '{command_str}'.")
        print_help()
        sys.exit(1)

    print(f"\n[Command Received]: '{command_str}'")
    print(f"Processing Priority [{dept_config['priority']}]: {dept_config['name']}")
    print("Single-department execution mode active. Next department will NOT start automatically.")

    engine = OdishaCorpusIngestionEngine(dept_config)
    result = engine.execute_lifecycle()

    print(f"Ingestion lifecycle finished with status: {result['status']}")
    print("Execution complete. STOPPING.\n")

if __name__ == "__main__":
    main()
