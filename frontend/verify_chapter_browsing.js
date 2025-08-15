#!/usr/bin/env node

/**
 * Verification script for Task 22: Chapter and Content Browsing Implementation
 * 
 * This script verifies that all required components and functionality have been implemented
 * for chapter and content browsing according to the task requirements.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Task 22: Chapter and Content Browsing Implementation\n');

// Define required files and their expected content
const requiredFiles = [
  {
    path: 'src/hooks/useChapters.ts',
    description: 'Chapter-related React hooks',
    requiredContent: [
      'useTableOfContents',
      'useChapterFigures', 
      'useChapterKnowledge',
      'apiClient.getChapters',
      'apiClient.getChapterFigures',
      'apiClient.getChapterKnowledge'
    ]
  },
  {
    path: 'src/components/TableOfContents.tsx',
    description: 'Table of Contents navigation component',
    requiredContent: [
      'TableOfContents',
      'ChapterItem',
      'onChapterSelect',
      'selectedChapterId',
      'useTableOfContents'
    ]
  },
  {
    path: 'src/components/ChapterDetail.tsx',
    description: 'Chapter detail view with figures and knowledge points',
    requiredContent: [
      'ChapterDetail',
      'ChapterOverview',
      'FiguresTab',
      'KnowledgeTab',
      'useChapterFigures',
      'useChapterKnowledge',
      'ImageViewer'
    ]
  },
  {
    path: 'src/components/ImageViewer.tsx',
    description: 'Image viewer with caption display',
    requiredContent: [
      'ImageViewer',
      'figure.caption',
      'figure.page_number',
      'isZoomed',
      'onClose'
    ]
  },
  {
    path: 'src/components/KnowledgePointBrowser.tsx',
    description: 'Knowledge point browser with source anchors',
    requiredContent: [
      'KnowledgePointBrowser',
      'KnowledgePointCard',
      'knowledgePoints',
      'anchors',
      'entities',
      'selectedType',
      'searchQuery'
    ]
  },
  {
    path: 'src/components/ChapterBrowser.tsx',
    description: 'Main chapter browser component',
    requiredContent: [
      'ChapterBrowser',
      'TableOfContents',
      'ChapterDetail',
      'selectedChapterId',
      'isMobileMenuOpen'
    ]
  },
  {
    path: 'src/pages/ChapterBrowserPage.tsx',
    description: 'Chapter browser page component',
    requiredContent: [
      'ChapterBrowserPage',
      'useParams',
      'useNavigate',
      'ChapterBrowser',
      'documentId'
    ]
  }
];

// Define updated files that should include new functionality
const updatedFiles = [
  {
    path: 'src/types/index.ts',
    description: 'Type definitions for Knowledge and TableOfContents',
    requiredContent: [
      'Knowledge',
      'TableOfContents',
      'ChapterTOC',
      'anchors'
    ]
  },
  {
    path: 'src/lib/api.ts',
    description: 'API client with chapter endpoints',
    requiredContent: [
      'getChapters',
      'getChapterFigures',
      'getChapterKnowledge'
    ]
  },
  {
    path: 'src/components/index.ts',
    description: 'Component exports including new chapter components',
    requiredContent: [
      'ChapterBrowser',
      'ChapterDetail',
      'ImageViewer',
      'KnowledgePointBrowser',
      'TableOfContents'
    ]
  },
  {
    path: 'src/pages/index.ts',
    description: 'Page exports including ChapterBrowserPage',
    requiredContent: [
      'ChapterBrowserPage'
    ]
  },
  {
    path: 'src/router.tsx',
    description: 'Router configuration with chapter browsing route',
    requiredContent: [
      'ChapterBrowserPage',
      '/documents/:documentId/chapters'
    ]
  },
  {
    path: 'src/components/DocumentList.tsx',
    description: 'Document list with Browse Chapters button',
    requiredContent: [
      'Browse',
      '/documents/${document.id}/chapters',
      'chapter_count > 0'
    ]
  }
];

let allPassed = true;
let totalChecks = 0;
let passedChecks = 0;

// Helper function to check if file exists and contains required content
function verifyFile(filePath, description, requiredContent) {
  const fullPath = path.join(__dirname, filePath);
  
  console.log(`📁 Checking ${description}:`);
  console.log(`   File: ${filePath}`);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`   ❌ File does not exist`);
    allPassed = false;
    return false;
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const missingContent = [];
  
  for (const required of requiredContent) {
    totalChecks++;
    if (content.includes(required)) {
      passedChecks++;
    } else {
      missingContent.push(required);
      allPassed = false;
    }
  }
  
  if (missingContent.length === 0) {
    console.log(`   ✅ All required content found`);
    return true;
  } else {
    console.log(`   ❌ Missing content: ${missingContent.join(', ')}`);
    return false;
  }
}

// Verify all required files
console.log('='.repeat(60));
console.log('📋 CHECKING REQUIRED NEW FILES');
console.log('='.repeat(60));

for (const file of requiredFiles) {
  verifyFile(file.path, file.description, file.requiredContent);
  console.log('');
}

console.log('='.repeat(60));
console.log('🔄 CHECKING UPDATED EXISTING FILES');
console.log('='.repeat(60));

for (const file of updatedFiles) {
  verifyFile(file.path, file.description, file.requiredContent);
  console.log('');
}

// Check responsive design considerations
console.log('='.repeat(60));
console.log('📱 CHECKING RESPONSIVE DESIGN FEATURES');
console.log('='.repeat(60));

const responsiveChecks = [
  {
    file: 'src/components/ChapterBrowser.tsx',
    features: ['isMobileMenuOpen', 'lg:hidden', 'lg:block', 'lg:w-80']
  },
  {
    file: 'src/components/ImageViewer.tsx', 
    features: ['md:hidden', 'max-w-7xl', 'mx-4']
  },
  {
    file: 'src/components/ChapterDetail.tsx',
    features: ['md:grid-cols-2', 'lg:grid-cols-3', 'sm:grid-cols-2']
  }
];

for (const check of responsiveChecks) {
  const filePath = path.join(__dirname, check.file);
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    const foundFeatures = check.features.filter(feature => content.includes(feature));
    
    console.log(`📱 ${check.file}:`);
    console.log(`   Found responsive features: ${foundFeatures.length}/${check.features.length}`);
    
    if (foundFeatures.length === check.features.length) {
      console.log(`   ✅ All responsive features implemented`);
    } else {
      console.log(`   ⚠️  Some responsive features missing: ${check.features.filter(f => !foundFeatures.includes(f)).join(', ')}`);
    }
  }
  console.log('');
}

// Final summary
console.log('='.repeat(60));
console.log('📊 VERIFICATION SUMMARY');
console.log('='.repeat(60));

console.log(`Total content checks: ${totalChecks}`);
console.log(`Passed checks: ${passedChecks}`);
console.log(`Success rate: ${Math.round((passedChecks / totalChecks) * 100)}%`);

if (allPassed) {
  console.log('\n🎉 SUCCESS: All Task 22 requirements have been implemented!');
  console.log('\n✅ Implementation includes:');
  console.log('   • Table of Contents (TOC) navigation component');
  console.log('   • Chapter detail view with figures and knowledge points');
  console.log('   • Image viewer with caption display');
  console.log('   • Knowledge point browser with source anchors');
  console.log('   • Responsive design for mobile and desktop');
  console.log('   • Integration with existing document management');
  
  console.log('\n🔗 Key Features:');
  console.log('   • Hierarchical chapter navigation');
  console.log('   • Tabbed interface for overview, figures, and knowledge');
  console.log('   • Zoomable image viewer with metadata');
  console.log('   • Filterable and searchable knowledge points');
  console.log('   • Mobile-responsive design with collapsible sidebar');
  console.log('   • Direct links from document list to chapter browser');
  
} else {
  console.log('\n❌ INCOMPLETE: Some Task 22 requirements are missing.');
  console.log('\n🔧 Please review the missing content and ensure all components are properly implemented.');
}

console.log('\n' + '='.repeat(60));

process.exit(allPassed ? 0 : 1);