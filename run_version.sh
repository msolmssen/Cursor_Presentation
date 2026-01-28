#!/bin/bash

# Launcher script to run different versions of the Outbound Engine
# Usage: ./run_version.sh [v1|v2|v3|...]

VERSION=${1:-v2}  # Default to v2 if no version specified

if [ "$VERSION" = "v1" ] || [ "$VERSION" = "V1" ]; then
    echo "🚀 Launching Outbound Engine V1..."
    cd versions/v1
    streamlit run app.py
elif [ "$VERSION" = "v2" ] || [ "$VERSION" = "V2" ]; then
    echo "🚀 Launching Outbound Engine V2 (current)..."
    streamlit run app.py
elif [ "$VERSION" = "v3" ] || [ "$VERSION" = "V3" ]; then
    echo "🚀 Launching Outbound Engine V3..."
    cd versions/v3
    streamlit run app.py
else
    # Check if version folder exists
    if [ -d "versions/$VERSION" ]; then
        echo "🚀 Launching Outbound Engine $VERSION..."
        cd versions/$VERSION
        streamlit run app.py
    else
        echo "❌ Version '$VERSION' not found!"
        echo ""
        echo "Available versions:"
        echo "  - v1 (in versions/v1/)"
        echo "  - v2 (current - root directory)"
        if [ -d "versions/v3" ]; then
            echo "  - v3 (in versions/v3/)"
        fi
        echo ""
        echo "Usage: ./run_version.sh [v1|v2|v3|...]"
        exit 1
    fi
fi
