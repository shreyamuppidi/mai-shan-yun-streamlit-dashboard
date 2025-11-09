#!/bin/bash
# Activate MSY virtual environment
# Usage: source activate_msy.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/msy/bin/activate"
echo "✅ MSY virtual environment activated"
echo "Python: $(which python)"
echo "Python version: $(python --version)"


