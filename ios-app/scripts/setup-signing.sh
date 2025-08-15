#!/bin/bash

# App Signing and Provisioning Profile Setup Script
# This script helps configure code signing for App Store deployment

set -e

echo "🔐 Setting up App Signing and Provisioning Profiles..."

# Check if we're in the correct directory
if [ ! -f "../package.json" ]; then
    echo "❌ Error: Please run this script from the ios-app/scripts directory"
    exit 1
fi

echo "📋 App Store Deployment Checklist:"
echo ""
echo "1. Apple Developer Account Setup:"
echo "   ✓ Ensure you have a valid Apple Developer Program membership"
echo "   ✓ Team ID: [TO BE CONFIGURED]"
echo "   ✓ Bundle ID: com.documentlearning.DocumentLearningApp"
echo ""
echo "2. Certificates Required:"
echo "   ✓ Apple Distribution Certificate"
echo "   ✓ iOS Distribution Certificate"
echo ""
echo "3. Provisioning Profiles:"
echo "   ✓ App Store Distribution Profile"
echo "   ✓ Profile Name: Document Learning App Store Profile"
echo ""
echo "4. App Store Connect Setup:"
echo "   ✓ App created in App Store Connect"
echo "   ✓ Bundle ID matches: com.documentlearning.DocumentLearningApp"
echo "   ✓ App metadata configured"
echo ""

# Function to update team ID
update_team_id() {
    local team_id=$1
    echo "🔧 Updating Team ID to: $team_id"
    
    # Update ExportOptions.plist
    sed -i '' "s/YOUR_TEAM_ID/$team_id/g" ../ios/ExportOptions.plist
    
    # Update project.pbxproj (would need actual implementation)
    echo "   ✓ Updated ExportOptions.plist"
    echo "   ⚠️  Please manually update DEVELOPMENT_TEAM in Xcode project settings"
}

# Function to validate signing setup
validate_signing() {
    echo "🔍 Validating signing setup..."
    
    # Check if certificates are installed
    if security find-identity -v -p codesigning | grep -q "Apple Distribution"; then
        echo "   ✓ Apple Distribution certificate found"
    else
        echo "   ❌ Apple Distribution certificate not found"
        echo "      Please install from Apple Developer Portal"
    fi
    
    # Check provisioning profiles
    if ls ~/Library/MobileDevice/Provisioning\ Profiles/*.mobileprovision 2>/dev/null | grep -q .; then
        echo "   ✓ Provisioning profiles found"
        echo "   📋 Installed profiles:"
        ls ~/Library/MobileDevice/Provisioning\ Profiles/*.mobileprovision 2>/dev/null | head -5
    else
        echo "   ❌ No provisioning profiles found"
        echo "      Please download from Apple Developer Portal"
    fi
}

# Interactive setup
echo "🛠️  Interactive Setup:"
echo ""
read -p "Enter your Apple Developer Team ID (or press Enter to skip): " team_id

if [ ! -z "$team_id" ]; then
    update_team_id "$team_id"
fi

echo ""
validate_signing

echo ""
echo "📝 Manual Steps Required:"
echo "1. Open ios/DocumentLearningApp.xcworkspace in Xcode"
echo "2. Select DocumentLearningApp target"
echo "3. Go to Signing & Capabilities tab"
echo "4. Set Team to your Apple Developer Team"
echo "5. Ensure 'Automatically manage signing' is checked"
echo "6. Verify Bundle Identifier: com.documentlearning.DocumentLearningApp"
echo "7. Set Provisioning Profile to 'Document Learning App Store Profile'"
echo ""
echo "✅ Signing setup guidance completed!"
echo "Run './build-release.sh' when signing is configured"