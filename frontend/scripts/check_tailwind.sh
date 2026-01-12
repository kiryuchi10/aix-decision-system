#!/bin/bash

echo "🔍 Checking Tailwind Configuration..."

if [ ! -f "tailwind.config.js" ]; then
    echo "❌ tailwind.config.js not found"
    exit 1
fi

if [ ! -f "postcss.config.js" ]; then
    echo "❌ postcss.config.js not found"
    exit 1
fi

if ! grep -q "@tailwind" src/index.css; then
    echo "❌ Tailwind directives not found in src/index.css"
    exit 1
fi

echo "✅ Tailwind is properly configured"
