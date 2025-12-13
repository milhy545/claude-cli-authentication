#!/usr/bin/env python3
"""
Environment Validation Script for Claude CLI Auth Project.

This script checks:
1. Node.js installation
2. Claude CLI (@anthropic-ai/claude-code) presence in PATH
3. Authentication state (claude auth whoami)

Usage:
    python scripts/check_env.py
"""

import sys
import shutil
import subprocess
import os

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"
    }
    prefix = f"[{status}]"
    print(f"{colors.get(status, '')}{prefix} {message}{colors['RESET']}")

def check_command(command, name):
    path = shutil.which(command)
    if path:
        print_status(f"Found {name} at: {path}", "SUCCESS")
        return path
    else:
        print_status(f"{name} ({command}) not found in PATH.", "ERROR")
        return None

def check_claude_auth():
    print_status("Checking Claude authentication status...", "INFO")
    try:
        # Run 'claude auth whoami'
        # We need to capture output to check for "not authenticated" messages
        # varying by version, but exit code 0 usually means success or at least CLI ran.
        result = subprocess.run(
            ["claude", "auth", "whoami"],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout.strip()
        stderr = result.stderr.strip()

        print_status(f"Output: {output}")
        if stderr:
            print_status(f"Stderr: {stderr}", "WARNING")

        if result.returncode == 0:
            # Heuristic check for success message
            # Adjust these strings based on actual CLI output if needed
            if "not authenticated" in output.lower() or "login" in output.lower():
                 print_status("Claude CLI is NOT authenticated. Please run 'claude auth login'.", "ERROR")
                 return False

            print_status("Claude CLI appears authenticated.", "SUCCESS")
            return True
        else:
             print_status(f"Claude auth check failed with exit code {result.returncode}.", "ERROR")
             return False

    except subprocess.TimeoutExpired:
        print_status("Claude auth check timed out.", "ERROR")
        return False
    except Exception as e:
        print_status(f"An unexpected error occurred: {e}", "ERROR")
        return False

def main():
    print_status("Starting Environment Sanity Check...", "INFO")

    # 1. Check Node.js (prerequisite for Claude CLI)
    if not check_command("node", "Node.js"):
        print_status("Node.js is required to run Claude CLI.", "ERROR")
        sys.exit(1)

    if not check_command("npm", "NPM"):
        print_status("NPM is required to install/update Claude CLI.", "WARNING")

    # 2. Check Claude CLI
    claude_path = check_command("claude", "Claude CLI")
    if not claude_path:
        print_status("Claude CLI package (@anthropic-ai/claude-code) is missing.", "ERROR")
        print_status("Install it using: npm install -g @anthropic-ai/claude-code", "INFO")
        sys.exit(1)

    # 3. Check Authentication
    if not check_claude_auth():
        print_status("Authentication check failed. Tests requiring live API will fail.", "ERROR")
        # We exit with error to ensure CI/pipeline stops here if this is a prerequisite
        sys.exit(1)

    print_status("Environment validation passed! 🚀", "SUCCESS")
    sys.exit(0)

if __name__ == "__main__":
    main()
