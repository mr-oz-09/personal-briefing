#!/bin/bash
set -e

# Build Lambda deployment package without Docker
# Usage: ./scripts/build-lambda.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/lambda"

echo "🔨 Building Lambda deployment package..."

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install dependencies to build directory using pip
cd "$PROJECT_ROOT"

# Install only runtime dependencies (excluding dev, test, and cdk deps)
pip install \
    -t "$BUILD_DIR" \
    --platform manylinux2014_x86_64 \
    --python-version 3.11 \
    --only-binary=:all: \
    boto3 \
    pydantic \
    pyyaml \
    requests

# Copy source code
cp -r "$PROJECT_ROOT/src/personal_briefing" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/"

# Create zip
cd "$BUILD_DIR"
zip -r ../lambda-package.zip . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"

echo "✅ Lambda package built: $PROJECT_ROOT/build/lambda-package.zip"
echo "📦 Size: $(du -h "$PROJECT_ROOT/build/lambda-package.zip" | cut -f1)"
