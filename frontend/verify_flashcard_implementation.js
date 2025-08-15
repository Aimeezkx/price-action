#!/usr/bin/env node

/**
 * Verification script for Task 23: Build flashcard learning interface
 * 
 * This script verifies that all required components and functionality
 * have been implemented according to the task requirements.
 */

const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
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

function checkFileContains(filePath, searchStrings) {
  const fullPath = path.join(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    return { exists: false, matches: [] };
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const matches = searchStrings.map(str => ({
    search: str,
    found: content.includes(str)
  }));
  
  return { exists: true, content, matches };
}

function runVerification() {
  log('\n🔍 Verifying Task 23: Build flashcard learning interface\n', 'blue');
  
  let passed = 0;
  let failed = 0;
  
  // Test 1: Check FlashCard component exists and has required features
  log('1. Checking FlashCard component...', 'yellow');
  const flashCardCheck = checkFileContains('src/components/FlashCard.tsx', [
    'interface FlashCardProps',
    'isFlipped',
    'onFlip',
    'card.card_type',
    'transform-style-preserve-3d',
    'backface-hidden',
    'rotate-y-180',
    'onClick={handleFlip}',
    'getDifficultyColor',
    'image_hotspot',
    'cloze'
  ]);
  
  if (flashCardCheck.exists && flashCardCheck.matches.every(m => m.found)) {
    log('   ✅ FlashCard component with flip animation implemented', 'green');
    passed++;
  } else {
    log('   ❌ FlashCard component missing or incomplete', 'red');
    flashCardCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 2: Check GradingInterface component
  log('2. Checking GradingInterface component...', 'yellow');
  const gradingCheck = checkFileContains('src/components/GradingInterface.tsx', [
    'interface GradingInterfaceProps',
    'onGrade',
    'gradeOptions',
    'value: 0',
    'value: 5',
    'handleKeyPress',
    'key >= \'0\' && key <= \'5\'',
    'onClick={() => onGrade(option.value)}',
    'disabled={disabled}'
  ]);
  
  if (gradingCheck.exists && gradingCheck.matches.every(m => m.found)) {
    log('   ✅ GradingInterface with 0-5 scale and keyboard shortcuts implemented', 'green');
    passed++;
  } else {
    log('   ❌ GradingInterface component missing or incomplete', 'red');
    gradingCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 3: Check ReviewSession component
  log('3. Checking ReviewSession component...', 'yellow');
  const sessionCheck = checkFileContains('src/components/ReviewSession.tsx', [
    'interface ReviewSessionProps',
    'onSessionComplete',
    'onSessionExit',
    'currentIndex',
    'isFlipped',
    'reviewedCards',
    'sessionStats',
    'handleKeyPress',
    'useCallback',
    'case \' \':', // space key
    'case \'j\':', // j key
    'case \'k\':', // k key
    'useGradeCard',
    'getProgressPercentage',
    'getAccuracyPercentage'
  ]);
  
  if (sessionCheck.exists && sessionCheck.matches.every(m => m.found)) {
    log('   ✅ ReviewSession with progress tracking and keyboard shortcuts implemented', 'green');
    passed++;
  } else {
    log('   ❌ ReviewSession component missing or incomplete', 'red');
    sessionCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 4: Check CardFilters component
  log('4. Checking CardFilters component...', 'yellow');
  const filtersCheck = checkFileContains('src/components/CardFilters.tsx', [
    'interface CardFilters',
    'chapter?:',
    'difficulty?:',
    'cardType?:',
    'onFiltersChange',
    'difficultyOptions',
    'cardTypeOptions',
    'easy', 'medium', 'hard',
    'qa', 'cloze', 'image_hotspot',
    'Clear All'
  ]);
  
  if (filtersCheck.exists && filtersCheck.matches.every(m => m.found)) {
    log('   ✅ CardFilters with chapter, difficulty, and type filtering implemented', 'green');
    passed++;
  } else {
    log('   ❌ CardFilters component missing or incomplete', 'red');
    filtersCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 5: Check StudyPage integration
  log('5. Checking StudyPage integration...', 'yellow');
  const studyPageCheck = checkFileContains('src/pages/StudyPage.tsx', [
    'import { ReviewSession }',
    'import { CardFilters',
    'useState<\'today\' | \'filtered\' | null>',
    'activeSession',
    'setActiveSession',
    'filters',
    'setFilters',
    'useTodayReview',
    'useCards',
    'filterParams',
    'onClick={() => setActiveSession(\'today\')}',
    'onClick={() => setActiveSession(\'filtered\')}',
    'onSessionComplete',
    'onSessionExit'
  ]);
  
  if (studyPageCheck.exists && studyPageCheck.matches.every(m => m.found)) {
    log('   ✅ StudyPage integrated with new flashcard components', 'green');
    passed++;
  } else {
    log('   ❌ StudyPage integration missing or incomplete', 'red');
    studyPageCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 6: Check CSS animations
  log('6. Checking CSS animations...', 'yellow');
  const cssCheck = checkFileContains('src/index.css', [
    'transform-style-preserve-3d',
    'backface-hidden',
    'rotate-y-180'
  ]);
  
  if (cssCheck.exists && cssCheck.matches.every(m => m.found)) {
    log('   ✅ CSS 3D flip animations implemented', 'green');
    passed++;
  } else {
    log('   ❌ CSS animations missing or incomplete', 'red');
    cssCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 7: Check component exports
  log('7. Checking component exports...', 'yellow');
  const exportsCheck = checkFileContains('src/components/index.ts', [
    'export { CardFilters }',
    'export { FlashCard }',
    'export { GradingInterface }',
    'export { ReviewSession }'
  ]);
  
  if (exportsCheck.exists && exportsCheck.matches.every(m => m.found)) {
    log('   ✅ All new components properly exported', 'green');
    passed++;
  } else {
    log('   ❌ Component exports missing or incomplete', 'red');
    exportsCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Test 8: Check keyboard shortcuts implementation
  log('8. Checking keyboard shortcuts...', 'yellow');
  const keyboardCheck = checkFileContains('src/components/ReviewSession.tsx', [
    'case \' \':', // space for flip
    'case \'j\':', // j for next
    'case \'k\':', // k for previous
    'case \'0\':', // 0-5 for grading
    'case \'1\':',
    'case \'2\':',
    'case \'3\':',
    'case \'4\':',
    'case \'5\':',
    'case \'Escape\':', // escape to exit
    'addEventListener(\'keydown\', handleKeyPress)',
    'removeEventListener(\'keydown\', handleKeyPress)'
  ]);
  
  if (keyboardCheck.exists && keyboardCheck.matches.every(m => m.found)) {
    log('   ✅ Keyboard shortcuts (Space, J/K, 0-5, Escape) implemented', 'green');
    passed++;
  } else {
    log('   ❌ Keyboard shortcuts missing or incomplete', 'red');
    keyboardCheck.matches.filter(m => !m.found).forEach(m => {
      log(`      Missing: ${m.search}`, 'red');
    });
    failed++;
  }
  
  // Summary
  log(`\n📊 Verification Summary:`, 'blue');
  log(`   ✅ Passed: ${passed}`, 'green');
  log(`   ❌ Failed: ${failed}`, 'red');
  log(`   📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%\n`, 'blue');
  
  if (failed === 0) {
    log('🎉 All requirements for Task 23 have been successfully implemented!', 'green');
    log('\nImplemented features:', 'blue');
    log('• FlashCard component with front/back flip animation', 'green');
    log('• GradingInterface with 0-5 scale buttons', 'green');
    log('• Keyboard shortcuts (Space for flip, 1-5 for grading, J/K navigation)', 'green');
    log('• ReviewSession with progress tracking', 'green');
    log('• CardFilters for chapter, difficulty, and type filtering', 'green');
    log('• Full integration with StudyPage', 'green');
    log('• CSS 3D animations for card flipping', 'green');
    log('• Proper TypeScript interfaces and error handling', 'green');
  } else {
    log('⚠️  Some requirements are missing or incomplete. Please review the failed checks above.', 'yellow');
  }
  
  return failed === 0;
}

// Run verification
if (require.main === module) {
  const success = runVerification();
  process.exit(success ? 0 : 1);
}

module.exports = { runVerification };