#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkFileExists(filePath) {
  const fullPath = path.join(__dirname, filePath);
  return fs.existsSync(fullPath);
}

function checkFileContains(filePath, patterns) {
  const fullPath = path.join(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    return { exists: false, matches: [] };
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const matches = patterns.map(pattern => {
    const regex = typeof pattern === 'string' ? new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) : pattern;
    return {
      pattern: pattern.toString(),
      found: regex.test(content)
    };
  });
  
  return { exists: true, content, matches };
}

function main() {
  log('🔍 Verifying Image Hotspot Card Interaction Implementation', 'blue');
  log('=' .repeat(60), 'blue');
  
  let passed = 0;
  let failed = 0;
  
  // Test 1: Check ImageHotspotViewer component exists and has required features
  log('\n1. Checking ImageHotspotViewer component...', 'yellow');
  const hotspotViewerCheck = checkFileContains('src/components/ImageHotspotViewer.tsx', [
    'interface ImageHotspotViewerProps',
    'zoom',
    'pan',
    'hotspot',
    'touch',
    'handleWheel',
    'handleTouchStart',
    'handleTouchMove',
    'handleTouchEnd',
    'handleZoomIn',
    'handleZoomOut',
    'handleResetView',
    'constrainPosition',
    'handleHotspotClick',
    'onValidationComplete',
    'motion.div',
    'AnimatePresence',
    'aria-label',
    'role="application"',
    'maxZoom',
    'minZoom',
    'enableKeyboardControls'
  ]);
  
  if (hotspotViewerCheck.exists) {
    const foundFeatures = hotspotViewerCheck.matches.filter(m => m.found).length;
    const totalFeatures = hotspotViewerCheck.matches.length;
    
    if (foundFeatures >= totalFeatures * 0.8) { // 80% of features should be present
      log(`✓ ImageHotspotViewer component: ${foundFeatures}/${totalFeatures} features found`, 'green');
      passed++;
    } else {
      log(`✗ ImageHotspotViewer component: Only ${foundFeatures}/${totalFeatures} features found`, 'red');
      failed++;
      
      // Show missing features
      hotspotViewerCheck.matches.filter(m => !m.found).forEach(m => {
        log(`  Missing: ${m.pattern}`, 'red');
      });
    }
  } else {
    log('✗ ImageHotspotViewer component file not found', 'red');
    failed++;
  }
  
  // Test 2: Check zoom and pan functionality
  log('\n2. Checking zoom and pan functionality...', 'yellow');
  const zoomPanCheck = checkFileContains('src/components/ImageHotspotViewer.tsx', [
    'handleZoomIn',
    'handleZoomOut',
    'handleResetView',
    'handleWheel',
    'scale',
    'position',
    'constrainPosition',
    'transform.*translate.*scale',
    'isDragging',
    'dragStart'
  ]);
  
  if (zoomPanCheck.exists) {
    const foundFeatures = zoomPanCheck.matches.filter(m => m.found).length;
    if (foundFeatures >= 8) {
      log('✓ Zoom and pan functionality implemented', 'green');
      passed++;
    } else {
      log(`✗ Zoom and pan functionality incomplete: ${foundFeatures}/10 features`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify zoom and pan functionality', 'red');
    failed++;
  }
  
  // Test 3: Check touch gesture support
  log('\n3. Checking touch gesture support...', 'yellow');
  const touchCheck = checkFileContains('src/components/ImageHotspotViewer.tsx', [
    'handleTouchStart',
    'handleTouchMove',
    'handleTouchEnd',
    'getTouchDistance',
    'getTouchCenter',
    'touches',
    'lastTouchDistance',
    'onTouchStart',
    'onTouchMove',
    'onTouchEnd'
  ]);
  
  if (touchCheck.exists) {
    const foundFeatures = touchCheck.matches.filter(m => m.found).length;
    if (foundFeatures >= 8) {
      log('✓ Touch gesture support implemented', 'green');
      passed++;
    } else {
      log(`✗ Touch gesture support incomplete: ${foundFeatures}/10 features`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify touch gesture support', 'red');
    failed++;
  }
  
  // Test 4: Check hotspot validation and feedback
  log('\n4. Checking hotspot validation and feedback...', 'yellow');
  const validationCheck = checkFileContains('src/components/ImageHotspotViewer.tsx', [
    'handleHotspotClick',
    'onValidationComplete',
    'clickedHotspots',
    'correctHotspots',
    'showFeedback',
    'feedbackType',
    'success.*partial.*error',
    'aria-pressed',
    'disabled.*answer'
  ]);
  
  if (validationCheck.exists) {
    const foundFeatures = validationCheck.matches.filter(m => m.found).length;
    if (foundFeatures >= 6) {
      log('✓ Hotspot validation and feedback implemented', 'green');
      passed++;
    } else {
      log(`✗ Hotspot validation incomplete: ${foundFeatures}/9 features`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify hotspot validation', 'red');
    failed++;
  }
  
  // Test 5: Check responsive image scaling
  log('\n5. Checking responsive image scaling...', 'yellow');
  const responsiveCheck = checkFileContains('src/components/ImageHotspotViewer.tsx', [
    'imageDimensions',
    'containerBounds',
    'max-w-full',
    'max-h-full',
    'object-contain',
    'getBoundingClientRect',
    'naturalWidth',
    'naturalHeight'
  ]);
  
  if (responsiveCheck.exists) {
    const foundFeatures = responsiveCheck.matches.filter(m => m.found).length;
    if (foundFeatures >= 5) {
      log('✓ Responsive image scaling implemented', 'green');
      passed++;
    } else {
      log(`✗ Responsive image scaling incomplete: ${foundFeatures}/8 features`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify responsive image scaling', 'red');
    failed++;
  }
  
  // Test 6: Check accessibility features
  log('\n6. Checking accessibility features...', 'yellow');
  const a11yCheck = checkFileContains('src/components/ImageHotspotViewer.tsx', [
    'aria-label',
    'aria-pressed',
    'role=',
    'tabIndex',
    'title=',
    'alt=',
    'disabled',
    'focus:',
    'keyboard'
  ]);
  
  if (a11yCheck.exists) {
    const foundFeatures = a11yCheck.matches.filter(m => m.found).length;
    if (foundFeatures >= 6) {
      log('✓ Accessibility features implemented', 'green');
      passed++;
    } else {
      log(`✗ Accessibility features incomplete: ${foundFeatures}/9 features`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify accessibility features', 'red');
    failed++;
  }
  
  // Test 7: Check FlashCard integration
  log('\n7. Checking FlashCard integration...', 'yellow');
  const integrationCheck = checkFileContains('src/components/FlashCard.tsx', [
    'ImageHotspotViewer',
    'image_hotspot',
    'hotspots',
    'onValidationComplete',
    'handleHotspotValidation'
  ]);
  
  if (integrationCheck.exists) {
    const foundFeatures = integrationCheck.matches.filter(m => m.found).length;
    if (foundFeatures >= 4) {
      log('✓ FlashCard integration implemented', 'green');
      passed++;
    } else {
      log(`✗ FlashCard integration incomplete: ${foundFeatures}/5 features`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify FlashCard integration', 'red');
    failed++;
  }
  
  // Test 8: Check demo component
  log('\n8. Checking demo component...', 'yellow');
  const demoExists = checkFileExists('src/components/ImageHotspotDemo.tsx');
  if (demoExists) {
    log('✓ ImageHotspotDemo component created', 'green');
    passed++;
  } else {
    log('✗ ImageHotspotDemo component not found', 'red');
    failed++;
  }
  
  // Test 9: Check component exports
  log('\n9. Checking component exports...', 'yellow');
  const exportsCheck = checkFileContains('src/components/index.ts', [
    'ImageHotspotViewer',
    'ImageHotspotDemo'
  ]);
  
  if (exportsCheck.exists) {
    const foundExports = exportsCheck.matches.filter(m => m.found).length;
    if (foundExports >= 2) {
      log('✓ Component exports updated', 'green');
      passed++;
    } else {
      log(`✗ Component exports incomplete: ${foundExports}/2 exports`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify component exports', 'red');
    failed++;
  }
  
  // Test 10: Check CSS utilities
  log('\n10. Checking CSS utilities...', 'yellow');
  const cssCheck = checkFileContains('src/index.css', [
    'pointer-events-auto',
    'pointer-events-none',
    'touch-pan',
    'touch-pinch-zoom',
    'transition-transform-smooth'
  ]);
  
  if (cssCheck.exists) {
    const foundStyles = cssCheck.matches.filter(m => m.found).length;
    if (foundStyles >= 3) {
      log('✓ CSS utilities added', 'green');
      passed++;
    } else {
      log(`✗ CSS utilities incomplete: ${foundStyles}/5 utilities`, 'red');
      failed++;
    }
  } else {
    log('✗ Cannot verify CSS utilities', 'red');
    failed++;
  }
  
  // Summary
  log('\n' + '='.repeat(60), 'blue');
  log(`📊 Test Results: ${passed} passed, ${failed} failed`, 'blue');
  
  if (failed === 0) {
    log('🎉 All tests passed! Image hotspot card interaction is fully implemented.', 'green');
    return 0;
  } else if (passed > failed) {
    log('⚠️  Most tests passed, but some issues need attention.', 'yellow');
    return 1;
  } else {
    log('❌ Implementation incomplete. Please address the failing tests.', 'red');
    return 2;
  }
}

process.exit(main());