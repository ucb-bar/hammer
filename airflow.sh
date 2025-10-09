#!/bin/bash
set -e  # exit on first error

# --- Set Airflow home ---
export AIRFLOW_HOME=$(pwd)
echo "AIRFLOW home directory set to: $AIRFLOW_HOME"

# --- Define versions ---
AIRFLOW_VERSION=3.0.2
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# --- Clean up doc-only packages that conflict with Airflow ---
echo "Removing doc-related packages to avoid version conflicts..."
pip uninstall -y myst-parser mdit-py-plugins markdown-it-py || true

# --- Install Airflow ---
echo "Installing Apache Airflow ${AIRFLOW_VERSION} (Python ${PYTHON_VERSION})"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

echo "Airflow installed successfully."
