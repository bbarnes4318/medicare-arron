#!/bin/bash

echo "============================================"
echo "Git Setup and Push to GitHub"
echo "============================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed"
    echo "Please install Git first"
    exit 1
fi

echo "Initializing Git repository..."
git init

echo ""
echo "Adding all files to Git..."
git add .

echo ""
echo "Committing files..."
git commit -m "Initial commit - Proxy Access Portal for DigitalOcean"

echo ""
echo "Adding GitHub remote..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/bbarnes4318/proxy.git

echo ""
echo "Setting branch to main..."
git branch -M main

echo ""
echo "Pushing to GitHub..."
git push -u origin main --force

echo ""
echo "============================================"
echo "DONE! Your code is now on GitHub"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Go to https://cloud.digitalocean.com/apps"
echo "2. Click 'Create App'"
echo "3. Select your GitHub repository: bbarnes4318/proxy"
echo "4. DigitalOcean will auto-detect the configuration"
echo "5. Click 'Deploy' and wait 3-5 minutes"
echo ""
echo "See DEPLOYMENT.md for detailed instructions"
echo "============================================"

