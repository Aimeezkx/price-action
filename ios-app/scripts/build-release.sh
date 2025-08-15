#!/bin/bash

# Build Release Version Script for iOS App Store Deployment
# This script builds the iOS app for App Store submission

set -e

echo "🚀 Building Document Learning App for App Store Release..."

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the ios-app directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Clean previous builds
echo "🧹 Cleaning previous builds..."
cd ios
xcodebuild clean -workspace DocumentLearningApp.xcworkspace -scheme DocumentLearningApp -configuration Release
cd ..

# Build React Native bundle for production
echo "📱 Building React Native bundle..."
npx react-native bundle \
    --platform ios \
    --dev false \
    --entry-file index.js \
    --bundle-output ios/main.jsbundle \
    --assets-dest ios/

# Build for App Store
echo "🏗️ Building for App Store..."
cd ios
xcodebuild archive \
    -workspace DocumentLearningApp.xcworkspace \
    -scheme DocumentLearningApp \
    -configuration Release \
    -archivePath build/DocumentLearningApp.xcarchive \
    -allowProvisioningUpdates

# Export for App Store
echo "📤 Exporting for App Store..."
xcodebuild -exportArchive \
    -archivePath build/DocumentLearningApp.xcarchive \
    -exportPath build/ \
    -exportOptionsPlist ExportOptions.plist

echo "✅ Build completed successfully!"
echo "📁 Archive location: ios/build/DocumentLearningApp.xcarchive"
echo "📁 IPA location: ios/build/DocumentLearningApp.ipa"
echo ""
echo "Next steps:"
echo "1. Upload to App Store Connect using Xcode or Application Loader"
echo "2. Submit for review through App Store Connect"