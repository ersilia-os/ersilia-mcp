#!/usr/bin/env bash
# Create the conda env this repo expects and install the project into it.
# Runs once, on codespace creation.
set -euo pipefail

ENV_NAME="ersilia-mcp"
PYTHON_VERSION="3.12"

conda init --bash

# The env name is load-bearing: .mcp.json starts the server with
# `conda run -n ersilia-mcp ersilia-mcp`.
if ! conda env list | grep -qE "^${ENV_NAME}\s"; then
  echo "Creating conda env ${ENV_NAME} (python ${PYTHON_VERSION})..."
  conda create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}"
fi

# poetry.toml sets virtualenvs.create = false, so Poetry installs directly
# into the conda env rather than building one of its own.
echo "Installing project dependencies..."
conda run --no-capture-output -n "${ENV_NAME}" pip install poetry
conda run --no-capture-output -n "${ENV_NAME}" poetry install --all-extras

# Land in the env on every new terminal.
if ! grep -q "conda activate ${ENV_NAME}" "${HOME}/.bashrc"; then
  echo "conda activate ${ENV_NAME}" >>"${HOME}/.bashrc"
fi

echo "Setup complete."
