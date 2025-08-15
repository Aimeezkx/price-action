#!/bin/bash

# TestFlight Beta Testing Setup Script
# This script helps configure TestFlight for beta testing

set -e

echo "🧪 Setting up TestFlight Beta Testing..."

# Check if we're in the correct directory
if [ ! -f "../package.json" ]; then
    echo "❌ Error: Please run this script from the ios-app/scripts directory"
    exit 1
fi

echo "📋 TestFlight Setup Checklist:"
echo ""
echo "1. App Store Connect Configuration:"
echo "   ✓ App created in App Store Connect"
echo "   ✓ Bundle ID: com.documentlearning.DocumentLearningApp"
echo "   ✓ TestFlight tab accessible"
echo ""
echo "2. Beta Testing Information:"
echo "   ✓ Beta App Description configured"
echo "   ✓ Beta App Review Information provided"
echo "   ✓ Test Information filled out"
echo ""
echo "3. Internal Testing Group:"
echo "   ✓ Internal testers added (up to 100)"
echo "   ✓ Team members with App Store Connect access"
echo ""
echo "4. External Testing Group:"
echo "   ✓ External testers added (up to 10,000)"
echo "   ✓ Beta App Review submitted (if required)"
echo ""

# Create TestFlight beta description
create_beta_description() {
    cat > ../app-store-metadata/testflight-description.md << 'EOF'
# TestFlight Beta Description

## What to Test

Welcome to the Document Learning App beta! Please help us test the following key features:

### Core Functionality
- [ ] Document upload (PDF, DOCX, Markdown)
- [ ] Automatic chapter recognition
- [ ] Image and caption pairing
- [ ] Knowledge point extraction
- [ ] Flashcard generation

### Study Features
- [ ] Flashcard review sessions
- [ ] Spaced repetition scheduling
- [ ] Grading system (0-5 scale)
- [ ] Progress tracking
- [ ] Study statistics

### Search & Discovery
- [ ] Full-text search
- [ ] Semantic search
- [ ] Filtering by chapter/difficulty/type
- [ ] Search history

### iOS-Specific Features
- [ ] Touch gestures and interactions
- [ ] Image hotspot cards
- [ ] Push notifications
- [ ] Offline functionality
- [ ] Siri Shortcuts

### Export & Integration
- [ ] Export to Anki format
- [ ] Export to Notion format
- [ ] JSONL backup/restore

## Known Issues
- Performance optimization ongoing for large documents
- Some edge cases in chapter recognition
- Minor UI adjustments needed for iPad

## Feedback Areas
Please provide feedback on:
1. User interface and experience
2. Performance and responsiveness
3. Feature completeness
4. Bug reports with reproduction steps
5. Suggestions for improvements

## How to Provide Feedback
- Use TestFlight's built-in feedback feature
- Email: beta@documentlearning.app
- Include device model and iOS version
- Provide detailed steps to reproduce issues

Thank you for helping us improve Document Learning!
EOF

    echo "   ✓ Created TestFlight beta description"
}

# Create beta testing guidelines
create_testing_guidelines() {
    cat > ../app-store-metadata/beta-testing-guidelines.md << 'EOF'
# Beta Testing Guidelines

## Test Scenarios

### Scenario 1: Document Upload and Processing
1. Upload a PDF document (5-20 pages)
2. Wait for processing to complete
3. Verify chapter structure is recognized
4. Check that images are properly extracted
5. Confirm knowledge points are identified

### Scenario 2: Flashcard Study Session
1. Navigate to generated flashcards
2. Start a study session
3. Review 10-15 cards
4. Test grading functionality (0-5 scale)
5. Verify spaced repetition scheduling

### Scenario 3: Search and Discovery
1. Use search to find specific topics
2. Test filtering options
3. Verify search results accuracy
4. Check search history functionality

### Scenario 4: Export Functionality
1. Export cards to Anki format
2. Export cards to Notion format
3. Create JSONL backup
4. Verify export file integrity

### Scenario 5: iOS-Specific Features
1. Test image hotspot interactions
2. Try Siri Shortcuts (if configured)
3. Test offline functionality
4. Verify push notifications

## Performance Testing
- Test with documents of various sizes (1MB to 50MB)
- Monitor app responsiveness during processing
- Check memory usage with large document sets
- Test battery impact during extended use

## Compatibility Testing
- Test on different iOS versions (iOS 12.4+)
- Test on various device sizes (iPhone SE to iPhone Pro Max)
- Test on iPad (if applicable)
- Test with different document types and languages

## Reporting Issues
When reporting issues, please include:
1. Device model and iOS version
2. App version and build number
3. Detailed steps to reproduce
4. Expected vs actual behavior
5. Screenshots or screen recordings if applicable
6. Document type and size (if relevant)

## Beta Testing Timeline
- Week 1-2: Core functionality testing
- Week 3: Performance and edge case testing
- Week 4: Final polish and bug fixes
- Week 5: Release candidate preparation
EOF

    echo "   ✓ Created beta testing guidelines"
}

# Create TestFlight release notes template
create_release_notes_template() {
    cat > ../app-store-metadata/testflight-release-notes-template.md << 'EOF'
# TestFlight Release Notes Template

## Build [BUILD_NUMBER] - [DATE]

### New Features
- [Feature 1 description]
- [Feature 2 description]

### Improvements
- [Improvement 1 description]
- [Improvement 2 description]

### Bug Fixes
- Fixed [bug description]
- Resolved [issue description]

### Known Issues
- [Known issue 1]
- [Known issue 2]

### Testing Focus
Please focus testing on:
- [Area 1 to test]
- [Area 2 to test]

### Feedback Needed
We especially need feedback on:
- [Specific feedback request 1]
- [Specific feedback request 2]

---
Thank you for beta testing Document Learning!
For support: beta@documentlearning.app
EOF

    echo "   ✓ Created release notes template"
}

# Main setup
echo "🛠️  Creating TestFlight configuration files..."
create_beta_description
create_testing_guidelines
create_release_notes_template

echo ""
echo "📝 Manual Steps Required in App Store Connect:"
echo ""
echo "1. Upload Build:"
echo "   - Build app using './build-release.sh'"
echo "   - Upload IPA to App Store Connect"
echo "   - Wait for processing to complete"
echo ""
echo "2. Configure TestFlight:"
echo "   - Go to TestFlight tab in App Store Connect"
echo "   - Select your build"
echo "   - Add beta app description from testflight-description.md"
echo "   - Configure test information"
echo ""
echo "3. Add Internal Testers:"
echo "   - Create internal testing group"
echo "   - Add team members with App Store Connect access"
echo "   - Enable automatic distribution (optional)"
echo ""
echo "4. Add External Testers (if needed):"
echo "   - Create external testing group"
echo "   - Add external testers by email"
echo "   - Submit for Beta App Review if required"
echo ""
echo "5. Distribute Build:"
echo "   - Select testers or groups"
echo "   - Add release notes for this build"
echo "   - Send invitations"
echo ""

echo "✅ TestFlight setup guidance completed!"
echo "📁 Configuration files created in app-store-metadata/"
echo ""
echo "Next steps:"
echo "1. Build and upload your app"
echo "2. Configure TestFlight in App Store Connect"
echo "3. Add testers and distribute builds"