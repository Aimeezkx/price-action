# iOS App Store Deployment Guide

This guide provides comprehensive instructions for deploying the Document Learning iOS app to the App Store.

## Prerequisites

### Development Environment
- macOS with Xcode 14.0 or later
- iOS 12.4+ deployment target
- Valid Apple Developer Program membership
- React Native 0.72+ development environment

### Apple Developer Account Setup
1. **Apple Developer Program Membership**
   - Individual or Organization account ($99/year)
   - Verify account status and team membership

2. **Bundle Identifier Registration**
   - Bundle ID: `com.documentlearning.DocumentLearningApp`
   - Register in Apple Developer Portal
   - Enable required capabilities (Push Notifications, Background App Refresh)

## Step 1: Configure App Signing and Provisioning

### Automatic Signing (Recommended)
1. Open `ios/DocumentLearningApp.xcworkspace` in Xcode
2. Select the DocumentLearningApp target
3. Go to "Signing & Capabilities" tab
4. Check "Automatically manage signing"
5. Select your development team
6. Verify Bundle Identifier matches: `com.documentlearning.DocumentLearningApp`

### Manual Signing (Advanced)
1. Create certificates in Apple Developer Portal:
   - iOS Distribution Certificate
   - Apple Distribution Certificate

2. Create provisioning profiles:
   - App Store Distribution Profile
   - Name: "Document Learning App Store Profile"

3. Run the signing setup script:
   ```bash
   cd ios-app/scripts
   ./setup-signing.sh
   ```

## Step 2: Create App Store Connect Listing

### App Information
1. Log in to [App Store Connect](https://appstoreconnect.apple.com)
2. Create new app with Bundle ID: `com.documentlearning.DocumentLearningApp`
3. Fill out app information:
   - **Name**: Document Learning
   - **Subtitle**: Transform documents into interactive flashcards
   - **Category**: Education
   - **Content Rating**: 4+ (No objectionable content)

### App Description
Use the content from `app-store-metadata/app-description.md`:
- Copy the app description
- Add keywords: flashcards, study, learning, documents, PDF, spaced repetition
- Set pricing (Free or Paid)

### Privacy Information
1. Complete Privacy Nutrition Labels
2. Add Privacy Policy URL: `https://documentlearning.app/privacy`
3. Configure data collection practices based on app functionality

## Step 3: Build Release Version

### Prepare Build Environment
1. Install dependencies:
   ```bash
   cd ios-app
   npm install
   cd ios && pod install && cd ..
   ```

2. Update version numbers:
   - Marketing Version: 1.0
   - Current Project Version: 1 (increment for each build)

### Build for App Store
Run the automated build script:
```bash
cd ios-app/scripts
./build-release.sh
```

Or build manually:
```bash
cd ios-app
npx react-native bundle --platform ios --dev false --entry-file index.js --bundle-output ios/main.jsbundle
cd ios
xcodebuild archive -workspace DocumentLearningApp.xcworkspace -scheme DocumentLearningApp -configuration Release -archivePath build/DocumentLearningApp.xcarchive
xcodebuild -exportArchive -archivePath build/DocumentLearningApp.xcarchive -exportPath build/ -exportOptionsPlist ExportOptions.plist
```

## Step 4: Set Up TestFlight Beta Testing

### Configure TestFlight
1. Run TestFlight setup script:
   ```bash
   cd ios-app/scripts
   ./testflight-setup.sh
   ```

2. Upload build to App Store Connect:
   - Use Xcode Organizer or Application Loader
   - Upload the generated IPA file
   - Wait for processing to complete

### Add Beta Testers
1. **Internal Testing** (up to 100 testers):
   - Add team members with App Store Connect access
   - No review required
   - Immediate distribution

2. **External Testing** (up to 10,000 testers):
   - Add external testers by email
   - Requires Beta App Review for first build
   - Use beta description from `app-store-metadata/testflight-description.md`

### Beta Testing Process
1. Distribute builds to internal testers first
2. Collect feedback and fix critical issues
3. Add external testers for broader testing
4. Iterate based on feedback
5. Prepare final release candidate

## Step 5: Prepare App Review Submission

### Create Review Materials
Run the app review preparation script:
```bash
cd ios-app/scripts
./app-review-preparation.sh
```

This creates:
- App review information template
- Review guidelines checklist
- Privacy policy template
- Screenshot guidelines
- App preview video guidelines
- Submission checklist

### Required Screenshots (8 total)
Create screenshots following the guidelines in `app-store-metadata/review-materials/screenshot-guidelines.md`:

1. Document upload interface
2. Chapter browsing with table of contents
3. Flashcard study session
4. Image hotspot interaction
5. Search and filtering interface
6. Study statistics and progress
7. iPad split-view interface
8. Settings and export options

### App Preview Video (Optional but Recommended)
Create a 15-30 second video showcasing:
- Document upload and processing
- Automatic flashcard generation
- Study session with spaced repetition
- Key features and benefits

## Step 6: Submit for App Review

### Pre-Submission Checklist
Use the checklist in `app-store-metadata/review-materials/submission-checklist.md`:

- [ ] All metadata completed
- [ ] Screenshots uploaded
- [ ] Privacy Policy accessible
- [ ] App tested thoroughly
- [ ] Review information provided
- [ ] Demo account created (if needed)

### Submission Process
1. Select your release build in App Store Connect
2. Complete all required metadata fields
3. Upload screenshots and app preview video
4. Set release options (manual or automatic)
5. Submit for review

### Review Timeline
- Initial review: 24-48 hours (typical)
- Standard review: 1-7 days
- Complex apps: Up to 7 days
- Expedited review: 1-2 days (if approved for expedited review)

## Step 7: Post-Submission

### Monitor Review Status
1. Check App Store Connect regularly
2. Respond to reviewer feedback promptly
3. Be prepared for potential rejection and resubmission

### Common Rejection Reasons
- App crashes or significant bugs
- Incomplete or misleading information
- Privacy Policy issues
- Screenshots don't represent actual app
- Design guideline violations

### Upon Approval
1. App becomes available on App Store (if automatic release)
2. Monitor initial user feedback and ratings
3. Plan post-launch marketing and updates

## Maintenance and Updates

### Version Updates
1. Increment version numbers appropriately
2. Update release notes for each version
3. Test thoroughly before submission
4. Consider phased release for major updates

### Ongoing Requirements
- Maintain Apple Developer Program membership
- Keep certificates and provisioning profiles current
- Respond to user feedback and reviews
- Comply with App Store guidelines changes

## Troubleshooting

### Common Build Issues
1. **Code Signing Errors**:
   - Verify team selection in Xcode
   - Check certificate validity
   - Regenerate provisioning profiles if needed

2. **Archive Failures**:
   - Clean build folder (Product → Clean Build Folder)
   - Check for missing dependencies
   - Verify React Native bundle generation

3. **Upload Issues**:
   - Check internet connection
   - Verify App Store Connect access
   - Try uploading from different network

### Support Resources
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)
- [React Native iOS Deployment Guide](https://reactnative.dev/docs/publishing-to-app-store)

## Scripts Reference

All deployment scripts are located in `ios-app/scripts/`:

- `setup-signing.sh` - Configure app signing and provisioning
- `build-release.sh` - Build release version for App Store
- `testflight-setup.sh` - Set up TestFlight beta testing
- `app-review-preparation.sh` - Prepare App Store review materials

## Contact and Support

For deployment issues or questions:
- Development Team: dev@documentlearning.app
- App Store Support: https://developer.apple.com/support/

---

**Note**: This guide assumes familiarity with iOS development and App Store processes. For first-time publishers, consider consulting Apple's official documentation and potentially working with an experienced iOS developer.