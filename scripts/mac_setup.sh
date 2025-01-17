#!/bin/bash

# Exit on errors
set -e

# Install required system packages
brew update
brew install git gdal gcc cairo glib tcl-tk mesa

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install Python dependencies
pip install --upgrade pip
pip install -r .devcontainer/requirements.txt

# Check if ~/.zshrc exists, create it if not
if [ ! -f ~/.zshrc ]; then
  touch ~/.zshrc
  echo "~/.zshrc not found, created a new one."
fi

# Add the current directory to PYTHONPATH in ~/.zshrc if not already present
if ! grep -q 'export PYTHONPATH="\$PYTHONPATH:\$PWD"' ~/.zshrc; then
  echo 'export PYTHONPATH="$PYTHONPATH:$PWD"' >> ~/.zshrc
fi

# Reload ~/.zshrc to apply the change
source ~/.zshrc

echo "Setup complete!"
echo "Activate the virtual environment with 'source venv/bin/activate' and run 'python3 pretty_gpx/main.py'."