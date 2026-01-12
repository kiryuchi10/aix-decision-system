#!/bin/bash

echo "🎨 Setting up AiX Frontend..."

# Install dependencies
echo "Installing dependencies..."
npm install

# Install Tailwind if not present
if ! grep -q "tailwindcss" package.json; then
    echo "Installing Tailwind CSS..."
    npm install -D tailwindcss postcss autoprefixer
    npx tailwindcss init -p
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "VITE_API_BASE_URL=http://localhost:8000" > .env
    echo "✅ Created .env file"
fi

# Verify Tailwind config
if [ ! -f "tailwind.config.js" ]; then
    echo "⚠️  tailwind.config.js not found. Please run: npx tailwindcss init -p"
fi

if [ ! -f "postcss.config.js" ]; then
    echo "⚠️  postcss.config.js not found. Please run: npx tailwindcss init -p"
fi

echo "✅ Frontend setup complete!"
echo "Start dev server with: npm run dev"
