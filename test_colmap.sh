#!/bin/bash

echo "Testing COLMAP Docker installation..."

# Test if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# Test if COLMAP image exists
if docker images | grep -q "colmap/colmap"; then
    echo "✅ COLMAP Docker image found"
else
    echo "⚠️ COLMAP image not found. Pulling..."
    docker pull colmap/colmap:latest
fi

# Test COLMAP command
echo "Testing COLMAP version..."
docker run --rm colmap/colmap:latest colmap -h | head -n 5

echo ""
echo "✅ COLMAP Docker is working correctly!" 