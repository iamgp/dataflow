#!/bin/bash
set -e

# Copy user files if provided
if [ -d "/evidence-workspace" ]; then
    echo "Evidence workspace mounted. Syncing user files..."

    # Copy pages directory if it exists
    if [ -d "/evidence-workspace/pages" ]; then
        echo "Syncing pages..."
        cp -r /evidence-workspace/pages/* /app/pages/
    fi

    # Copy sources directory if it exists
    if [ -d "/evidence-workspace/sources" ]; then
        echo "Syncing sources..."
        cp -r /evidence-workspace/sources/* /app/sources/
    fi

    # Copy any custom components or other directories
    for dir in components static; do
        if [ -d "/evidence-workspace/$dir" ]; then
            echo "Syncing $dir..."
            cp -r "/evidence-workspace/$dir"/* "/app/$dir"/
        fi
    done
fi

# Start the development server
echo "Starting Evidence development server..."
cd /app
npm run dev -- --host 0.0.0.0
