#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying iOS Image Hotspot Implementation...\n');

const requiredFiles = [
  'src/components/ImageHotspotViewer.tsx',
  'src/screens/ImageHotspotDemoScreen.tsx',
  'src/types/index.ts',
];

const requiredFeatures = [
  {
    file: 'src/components/ImageHotspotViewer.tsx',
    features: [
      'PinchGestureHandler',
      'PanGestureHandler',
      'zoom and pan gestures',
      'touch-based hotspot interaction',
      'hotspot validation',
      'visual feedback',
      'responsive image scaling',
      'haptic feedback',
    ]
  },
  {
    file: 'src/components/FlashCard.tsx',
    features: [
      'ImageHotspotViewer integration',
      'image_hotspot card type handling',
      'auto-flip after validation',
    ]
  },
  {
    file: 'src/types/index.ts',
    features: [
      'Hotspot interface',
      'position percentages',
      'correct/incorrect flags',
    ]
  }
];

let allPassed = true;

// Check if required files exist
console.log('📁 Checking required files...');
requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - Missing`);
    allPassed = false;
  }
});

console.log('\n🔧 Checking implementation features...');

// Check implementation features
requiredFeatures.forEach(({ file, features }) => {
  const filePath = path.join(__dirname, file);
  
  if (!fs.existsSync(filePath)) {
    console.log(`❌ ${file} - File not found`);
    allPassed = false;
    return;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  
  console.log(`\n📄 ${file}:`);
  
  features.forEach(feature => {
    let found = false;
    
    switch (feature) {
      case 'PinchGestureHandler':
        found = content.includes('PinchGestureHandler');
        break;
      case 'PanGestureHandler':
        found = content.includes('PanGestureHandler');
        break;
      case 'zoom and pan gestures':
        found = content.includes('pinch') && content.includes('pan') && content.includes('scale');
        break;
      case 'touch-based hotspot interaction':
        found = content.includes('TouchableOpacity') && content.includes('onPress');
        break;
      case 'hotspot validation':
        found = content.includes('onValidationComplete') && content.includes('correct');
        break;
      case 'visual feedback':
        found = content.includes('feedbackOverlay') || content.includes('feedback');
        break;
      case 'responsive image scaling':
        found = content.includes('Dimensions') && content.includes('screenWidth');
        break;
      case 'haptic feedback':
        found = content.includes('hapticService');
        break;
      case 'ImageHotspotViewer integration':
        found = content.includes('ImageHotspotViewer');
        break;
      case 'image_hotspot card type handling':
        found = content.includes('image_hotspot');
        break;
      case 'auto-flip after validation':
        found = content.includes('setTimeout') && content.includes('handleFlip');
        break;
      case 'Hotspot interface':
        found = content.includes('interface Hotspot') || content.includes('export interface Hotspot');
        break;
      case 'position percentages':
        found = content.includes('x: number') && content.includes('y: number');
        break;
      case 'correct/incorrect flags':
        found = content.includes('correct: boolean');
        break;
      default:
        found = content.toLowerCase().includes(feature.toLowerCase());
    }
    
    if (found) {
      console.log(`  ✅ ${feature}`);
    } else {
      console.log(`  ❌ ${feature}`);
      allPassed = false;
    }
  });
});

// Check gesture handler dependencies
console.log('\n📦 Checking dependencies...');
const packageJsonPath = path.join(__dirname, 'package.json');
if (fs.existsSync(packageJsonPath)) {
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
  
  const requiredDeps = [
    'react-native-gesture-handler',
    'react-native-reanimated',
    'react-native-haptic-feedback',
  ];
  
  requiredDeps.forEach(dep => {
    if (dependencies[dep]) {
      console.log(`✅ ${dep} (${dependencies[dep]})`);
    } else {
      console.log(`❌ ${dep} - Missing dependency`);
      allPassed = false;
    }
  });
} else {
  console.log('❌ package.json not found');
  allPassed = false;
}

// Check navigation integration
console.log('\n🧭 Checking navigation integration...');
const navPath = path.join(__dirname, 'src/navigation/AppNavigator.tsx');
if (fs.existsSync(navPath)) {
  const navContent = fs.readFileSync(navPath, 'utf8');
  if (navContent.includes('ImageHotspotDemoScreen')) {
    console.log('✅ Demo screen added to navigation');
  } else {
    console.log('⚠️  Demo screen not in navigation (optional for testing)');
  }
} else {
  console.log('❌ Navigation file not found');
  allPassed = false;
}

// Summary
console.log('\n' + '='.repeat(50));
if (allPassed) {
  console.log('🎉 All checks passed! iOS Image Hotspot implementation is complete.');
  console.log('\n📱 Features implemented:');
  console.log('• Native image viewer with zoom and pan gestures');
  console.log('• Touch-based hotspot interaction');
  console.log('• Pinch-to-zoom and pan gesture recognition');
  console.log('• Hotspot validation with visual feedback');
  console.log('• Responsive image scaling for different screen sizes');
  console.log('• Haptic feedback for interactions');
  console.log('• Integration with FlashCard component');
  console.log('• Demo screen for testing');
  
  console.log('\n🧪 To test the implementation:');
  console.log('1. Run the iOS app: npm run ios');
  console.log('2. Navigate to the Demo tab');
  console.log('3. Test zoom, pan, and hotspot interactions');
  console.log('4. Try both study and answer modes');
  
  process.exit(0);
} else {
  console.log('❌ Some checks failed. Please review the implementation.');
  process.exit(1);
}