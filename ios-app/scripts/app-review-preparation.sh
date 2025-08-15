#!/bin/bash

# App Review Submission Preparation Script
# This script helps prepare materials for App Store review

set -e

echo "📝 Preparing App Store Review Submission Materials..."

# Check if we're in the correct directory
if [ ! -f "../package.json" ]; then
    echo "❌ Error: Please run this script from the ios-app/scripts directory"
    exit 1
fi

# Create app review materials
create_review_materials() {
    mkdir -p ../app-store-metadata/review-materials
    
    # App Review Information
    cat > ../app-store-metadata/review-materials/app-review-information.md << 'EOF'
# App Review Information

## Contact Information
- First Name: [YOUR_FIRST_NAME]
- Last Name: [YOUR_LAST_NAME]
- Phone Number: [YOUR_PHONE_NUMBER]
- Email: [YOUR_EMAIL]

## Demo Account (if required)
- Username: demo@documentlearning.app
- Password: DemoUser2024!
- Notes: Demo account with sample documents pre-loaded

## Review Notes
This app transforms documents (PDF, DOCX, Markdown) into interactive flashcards using AI-powered content extraction and spaced repetition learning.

### Key Features to Review:
1. Document upload and processing
2. Automatic flashcard generation
3. Spaced repetition study system
4. Search and filtering capabilities
5. Export functionality

### Privacy Considerations:
- App processes documents locally when privacy mode is enabled
- No personal data is transmitted without user consent
- Users can choose between local and cloud processing
- All document content remains under user control

### Third-Party Content:
- Uses open-source libraries listed in acknowledgments
- No third-party content or user-generated content
- All sample documents are created by the development team

## Attachments
- Screenshots (8 required)
- App Preview video (optional but recommended)
- Privacy Policy document
- Terms of Service document
EOF

    # App Store Review Guidelines Checklist
    cat > ../app-store-metadata/review-materials/review-guidelines-checklist.md << 'EOF'
# App Store Review Guidelines Checklist

## Safety (Guideline 1)
- [x] App does not contain objectionable content
- [x] No user-generated content that could be inappropriate
- [x] No violence, harassment, or illegal activities
- [x] Child safety considerations addressed

## Performance (Guideline 2)
- [x] App functions as described
- [x] No crashes or major bugs
- [x] Reasonable loading times
- [x] Proper error handling
- [x] Works on all supported devices and iOS versions

## Business (Guideline 3)
- [x] App provides value to users
- [x] No spam or copycat functionality
- [x] Proper pricing (if applicable)
- [x] No misleading app information

## Design (Guideline 4)
- [x] Follows iOS Human Interface Guidelines
- [x] Native iOS experience
- [x] Proper use of iOS features
- [x] Accessibility support
- [x] Consistent user interface

## Legal (Guideline 5)
- [x] Privacy Policy provided and accessible
- [x] Terms of Service provided
- [x] Proper data handling and user consent
- [x] No copyright infringement
- [x] Appropriate content ratings

## Privacy (App Store Connect)
- [x] Privacy nutrition labels completed
- [x] Data collection practices disclosed
- [x] User consent mechanisms implemented
- [x] Data minimization principles followed

## Metadata
- [x] Accurate app description
- [x] Appropriate keywords
- [x] Correct category selection
- [x] Age rating appropriate
- [x] Screenshots represent actual app functionality
EOF

    # Privacy Policy Template
    cat > ../app-store-metadata/review-materials/privacy-policy.md << 'EOF'
# Privacy Policy - Document Learning App

Last updated: [DATE]

## Introduction
Document Learning ("we," "our," or "us") respects your privacy and is committed to protecting your personal information. This Privacy Policy explains how we collect, use, and safeguard your information when you use our mobile application.

## Information We Collect

### Documents and Content
- Documents you upload (PDFs, DOCX, Markdown files)
- Generated flashcards and study materials
- Study progress and performance data
- Search queries and app usage patterns

### Device Information
- Device type and operating system version
- App version and crash reports
- Performance and usage analytics (anonymized)

### Optional Cloud Services
- If you choose to use cloud features, we may store your data on secure servers
- You can opt for local-only processing to keep all data on your device

## How We Use Your Information

### Core Functionality
- Process documents to extract learning content
- Generate personalized flashcards
- Track study progress and spaced repetition
- Provide search and filtering capabilities

### App Improvement
- Analyze usage patterns to improve features
- Fix bugs and enhance performance
- Develop new functionality based on user needs

## Data Storage and Security

### Local Storage
- By default, all data is stored locally on your device
- You control when and if data is shared or backed up

### Cloud Storage (Optional)
- Encrypted transmission and storage
- Industry-standard security measures
- You can delete cloud data at any time

### Data Retention
- Local data remains until you delete the app
- Cloud data is deleted when you request account deletion
- Anonymized analytics may be retained for app improvement

## Your Rights and Choices

### Privacy Mode
- Enable local-only processing
- No data transmission to external services
- Complete control over your documents and study data

### Data Export
- Export your flashcards and study data
- Compatible formats for other applications
- Full data portability

### Data Deletion
- Delete individual documents or all app data
- Request deletion of cloud-stored data
- Clear study history and progress

## Third-Party Services
We may use third-party services for:
- Crash reporting and analytics (anonymized)
- Cloud storage (if you opt-in)
- AI processing (if you choose cloud-based features)

All third-party services are bound by strict privacy agreements.

## Children's Privacy
Our app is not directed to children under 13. We do not knowingly collect personal information from children under 13.

## Changes to This Policy
We may update this Privacy Policy periodically. We will notify you of significant changes through the app or other means.

## Contact Us
If you have questions about this Privacy Policy:
- Email: privacy@documentlearning.app
- Website: https://documentlearning.app/privacy

## Consent
By using Document Learning, you consent to this Privacy Policy.
EOF

    echo "   ✓ Created app review information template"
    echo "   ✓ Created review guidelines checklist"
    echo "   ✓ Created privacy policy template"
}

# Create screenshot guidelines
create_screenshot_guidelines() {
    cat > ../app-store-metadata/review-materials/screenshot-guidelines.md << 'EOF'
# App Store Screenshot Guidelines

## Required Screenshots (8 total)

### iPhone Screenshots (6.5" Display - iPhone 14 Pro Max)
1. **Document Upload Screen**
   - Show drag-and-drop interface
   - Display supported file types
   - Include upload progress indicator

2. **Chapter Browser**
   - Display table of contents
   - Show chapter hierarchy
   - Include navigation elements

3. **Flashcard Study Session**
   - Show flashcard front/back
   - Display grading interface (0-5 scale)
   - Include progress indicators

4. **Image Hotspot Interaction**
   - Show image with clickable hotspots
   - Demonstrate touch interaction
   - Display caption or explanation

5. **Search Interface**
   - Show search input with suggestions
   - Display filtered results
   - Include search history

6. **Study Statistics**
   - Show progress charts
   - Display study streaks
   - Include performance metrics

### iPad Screenshots (12.9" Display - iPad Pro)
7. **Split View Interface**
   - Show document and flashcards side-by-side
   - Demonstrate iPad-optimized layout
   - Include multitasking features

8. **Settings and Export**
   - Show privacy settings
   - Display export options
   - Include app preferences

## Screenshot Requirements
- Use actual app content (no mockups)
- Show realistic data and interactions
- Include proper status bars and navigation
- Use high-quality, crisp images
- Avoid excessive text overlays
- Demonstrate key app features
- Show the app in use, not just static screens

## Image Specifications
- iPhone 6.5": 1284 x 2778 pixels
- iPad 12.9": 2048 x 2732 pixels
- Format: PNG or JPEG
- Color space: sRGB or P3
- No transparency or rounded corners

## Localization
If supporting multiple languages:
- Provide screenshots in each supported language
- Ensure text is properly translated
- Maintain consistent visual design across languages
EOF

    echo "   ✓ Created screenshot guidelines"
}

# Create app preview video guidelines
create_video_guidelines() {
    cat > ../app-store-metadata/review-materials/app-preview-guidelines.md << 'EOF'
# App Preview Video Guidelines

## Video Specifications
- Duration: 15-30 seconds
- Resolution: 1080p or higher
- Format: MOV or MP4
- Frame rate: 30 fps
- Orientation: Portrait for iPhone, Landscape for iPad

## Content Structure (30-second version)

### Seconds 0-5: Document Upload
- Show user selecting and uploading a PDF
- Display processing indicator
- Quick transition to processed content

### Seconds 5-15: Flashcard Generation
- Show automatically generated flashcards
- Demonstrate different card types (Q&A, cloze, image hotspot)
- Quick preview of study interface

### Seconds 15-25: Study Session
- Show user studying flashcards
- Demonstrate grading system
- Show spaced repetition scheduling

### Seconds 25-30: Key Features
- Quick montage of search, export, and statistics
- End with app logo and tagline

## Production Guidelines
- Use actual app footage (no animations or mockups)
- Show realistic user interactions
- Include device frames for context
- Use smooth transitions between scenes
- No external audio or voiceover
- Focus on core value proposition

## Content Requirements
- Must represent actual app functionality
- No misleading or exaggerated features
- Show the app as users will experience it
- Include proper iOS interface elements
- Demonstrate key differentiating features

## Technical Considerations
- Record on actual devices
- Use high-quality screen recording
- Ensure smooth playback
- Test on different connection speeds
- Optimize file size for streaming

## Localization
- Create versions for each supported language
- Ensure UI text is properly translated
- Maintain consistent pacing across versions
EOF

    echo "   ✓ Created app preview video guidelines"
}

# Create submission checklist
create_submission_checklist() {
    cat > ../app-store-metadata/review-materials/submission-checklist.md << 'EOF'
# App Store Submission Checklist

## Pre-Submission Requirements

### App Store Connect Setup
- [ ] App created with correct Bundle ID
- [ ] App information completed
- [ ] Pricing and availability configured
- [ ] Age rating completed
- [ ] Privacy nutrition labels filled out

### Build Preparation
- [ ] Release build created and tested
- [ ] All features working as expected
- [ ] Performance optimized
- [ ] Memory leaks resolved
- [ ] Crash-free operation verified

### Metadata Completion
- [ ] App name and subtitle finalized
- [ ] App description written and reviewed
- [ ] Keywords researched and selected
- [ ] Category and subcategory chosen
- [ ] Screenshots captured and uploaded
- [ ] App preview video created (optional)

### Legal Requirements
- [ ] Privacy Policy created and accessible
- [ ] Terms of Service created (if applicable)
- [ ] Copyright and trademark compliance verified
- [ ] Content rating appropriate for target audience

### Review Information
- [ ] Contact information provided
- [ ] Demo account created (if required)
- [ ] Review notes written
- [ ] Special instructions documented

## Submission Process

### Final Testing
- [ ] Test on multiple devices and iOS versions
- [ ] Verify all features work offline
- [ ] Test with various document types and sizes
- [ ] Confirm export functionality works
- [ ] Validate search and filtering features

### App Store Connect Submission
- [ ] Select build for release
- [ ] Complete all required metadata fields
- [ ] Upload all required screenshots
- [ ] Add app preview video (if created)
- [ ] Set release options (manual/automatic)
- [ ] Submit for review

### Post-Submission
- [ ] Monitor review status
- [ ] Respond to reviewer feedback promptly
- [ ] Prepare for potential rejection and resubmission
- [ ] Plan marketing and launch activities

## Common Rejection Reasons to Avoid
- [ ] App crashes or has significant bugs
- [ ] Incomplete or misleading app information
- [ ] Privacy Policy missing or inadequate
- [ ] Screenshots don't represent actual app
- [ ] App doesn't function as described
- [ ] Violation of design guidelines
- [ ] Inappropriate content rating
- [ ] Missing required permissions explanations

## Review Timeline
- Initial review: 24-48 hours (typical)
- Standard review: 1-7 days
- Complex apps: Up to 7 days
- Expedited review: 1-2 days (if approved)

## Success Metrics
- [ ] App approved on first submission
- [ ] No major issues identified
- [ ] Positive reviewer feedback
- [ ] Ready for public release
EOF

    echo "   ✓ Created submission checklist"
}

# Main execution
echo "🛠️  Creating App Store review materials..."
create_review_materials
create_screenshot_guidelines
create_video_guidelines
create_submission_checklist

echo ""
echo "📋 Review Preparation Summary:"
echo ""
echo "Created files:"
echo "   📄 app-review-information.md - Contact info and demo account"
echo "   ✅ review-guidelines-checklist.md - Compliance checklist"
echo "   🔒 privacy-policy.md - Privacy policy template"
echo "   📸 screenshot-guidelines.md - Screenshot requirements"
echo "   🎥 app-preview-guidelines.md - Video creation guide"
echo "   📝 submission-checklist.md - Complete submission checklist"
echo ""
echo "📝 Next Steps:"
echo "1. Customize templates with your information"
echo "2. Create required screenshots and video"
echo "3. Complete App Store Connect metadata"
echo "4. Test thoroughly on multiple devices"
echo "5. Submit for review"
echo ""
echo "✅ App review preparation completed!"
echo "📁 All materials saved in app-store-metadata/review-materials/"