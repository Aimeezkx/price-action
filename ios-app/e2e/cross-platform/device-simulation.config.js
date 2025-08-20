/**
 * iOS Device Simulation Configuration
 * Defines different device configurations for comprehensive testing
 */

const deviceConfigurations = {
  // iPhone devices
  iphone_se: {
    name: 'iPhone SE (3rd generation)',
    type: 'ios.simulator',
    device: {
      type: 'iPhone SE (3rd generation)'
    },
    screenSize: { width: 375, height: 667 },
    pixelRatio: 2,
    capabilities: ['touch', 'accelerometer', 'gyroscope']
  },
  
  iphone_14: {
    name: 'iPhone 14',
    type: 'ios.simulator',
    device: {
      type: 'iPhone 14'
    },
    screenSize: { width: 390, height: 844 },
    pixelRatio: 3,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'face_id']
  },
  
  iphone_14_pro: {
    name: 'iPhone 14 Pro',
    type: 'ios.simulator',
    device: {
      type: 'iPhone 14 Pro'
    },
    screenSize: { width: 393, height: 852 },
    pixelRatio: 3,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'face_id', 'dynamic_island']
  },
  
  iphone_14_pro_max: {
    name: 'iPhone 14 Pro Max',
    type: 'ios.simulator',
    device: {
      type: 'iPhone 14 Pro Max'
    },
    screenSize: { width: 430, height: 932 },
    pixelRatio: 3,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'face_id', 'dynamic_island']
  },
  
  // iPad devices
  ipad_10th_gen: {
    name: 'iPad (10th generation)',
    type: 'ios.simulator',
    device: {
      type: 'iPad (10th generation)'
    },
    screenSize: { width: 820, height: 1180 },
    pixelRatio: 2,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'split_view', 'slide_over']
  },
  
  ipad_air_5th: {
    name: 'iPad Air (5th generation)',
    type: 'ios.simulator',
    device: {
      type: 'iPad Air (5th generation)'
    },
    screenSize: { width: 820, height: 1180 },
    pixelRatio: 2,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'split_view', 'slide_over', 'apple_pencil']
  },
  
  ipad_pro_11: {
    name: 'iPad Pro (11-inch)',
    type: 'ios.simulator',
    device: {
      type: 'iPad Pro (11-inch) (4th generation)'
    },
    screenSize: { width: 834, height: 1194 },
    pixelRatio: 2,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'split_view', 'slide_over', 'apple_pencil', 'face_id']
  },
  
  ipad_pro_12_9: {
    name: 'iPad Pro (12.9-inch)',
    type: 'ios.simulator',
    device: {
      type: 'iPad Pro (12.9-inch) (6th generation)'
    },
    screenSize: { width: 1024, height: 1366 },
    pixelRatio: 2,
    capabilities: ['touch', 'accelerometer', 'gyroscope', 'split_view', 'slide_over', 'apple_pencil', 'face_id']
  }
};

// Test scenarios for different device categories
const testScenarios = {
  compact_devices: ['iphone_se', 'iphone_14'],
  standard_devices: ['iphone_14_pro', 'iphone_14_pro_max'],
  tablet_devices: ['ipad_10th_gen', 'ipad_air_5th'],
  pro_devices: ['ipad_pro_11', 'ipad_pro_12_9'],
  all_devices: Object.keys(deviceConfigurations)
};

// Network conditions for testing
const networkConditions = {
  wifi: {
    speed: 'full',
    latency: 10
  },
  cellular_4g: {
    speed: '4g',
    latency: 50
  },
  cellular_3g: {
    speed: '3g',
    latency: 100
  },
  slow_connection: {
    speed: 'slow-3g',
    latency: 200
  },
  offline: {
    offline: true
  }
};

// Accessibility configurations
const accessibilityConfigurations = {
  default: {
    voiceOver: false,
    dynamicType: 'medium',
    reduceMotion: false,
    increaseContrast: false
  },
  voiceOver: {
    voiceOver: true,
    dynamicType: 'medium',
    reduceMotion: false,
    increaseContrast: false
  },
  largeText: {
    voiceOver: false,
    dynamicType: 'xxxLarge',
    reduceMotion: false,
    increaseContrast: false
  },
  reducedMotion: {
    voiceOver: false,
    dynamicType: 'medium',
    reduceMotion: true,
    increaseContrast: false
  },
  highContrast: {
    voiceOver: false,
    dynamicType: 'medium',
    reduceMotion: false,
    increaseContrast: true
  }
};

// Performance thresholds for different device categories
const performanceThresholds = {
  compact_devices: {
    appLaunchTime: 6000, // 6 seconds
    navigationTime: 1500, // 1.5 seconds
    documentProcessingTime: 45000, // 45 seconds
    memoryUsage: 150 * 1024 * 1024 // 150MB
  },
  standard_devices: {
    appLaunchTime: 4000, // 4 seconds
    navigationTime: 1000, // 1 second
    documentProcessingTime: 30000, // 30 seconds
    memoryUsage: 200 * 1024 * 1024 // 200MB
  },
  tablet_devices: {
    appLaunchTime: 3000, // 3 seconds
    navigationTime: 800, // 0.8 seconds
    documentProcessingTime: 25000, // 25 seconds
    memoryUsage: 300 * 1024 * 1024 // 300MB
  },
  pro_devices: {
    appLaunchTime: 2500, // 2.5 seconds
    navigationTime: 600, // 0.6 seconds
    documentProcessingTime: 20000, // 20 seconds
    memoryUsage: 500 * 1024 * 1024 // 500MB
  }
};

// Helper functions
function getDeviceConfiguration(deviceKey) {
  return deviceConfigurations[deviceKey];
}

function getDevicesForScenario(scenarioKey) {
  return testScenarios[scenarioKey] || [];
}

function getPerformanceThreshold(deviceKey, metric) {
  // Determine device category
  let category = 'standard_devices';
  
  if (testScenarios.compact_devices.includes(deviceKey)) {
    category = 'compact_devices';
  } else if (testScenarios.tablet_devices.includes(deviceKey)) {
    category = 'tablet_devices';
  } else if (testScenarios.pro_devices.includes(deviceKey)) {
    category = 'pro_devices';
  }
  
  return performanceThresholds[category][metric];
}

function isTabletDevice(deviceKey) {
  return testScenarios.tablet_devices.includes(deviceKey) || 
         testScenarios.pro_devices.includes(deviceKey);
}

function hasCapability(deviceKey, capability) {
  const device = deviceConfigurations[deviceKey];
  return device && device.capabilities.includes(capability);
}

module.exports = {
  deviceConfigurations,
  testScenarios,
  networkConditions,
  accessibilityConfigurations,
  performanceThresholds,
  getDeviceConfiguration,
  getDevicesForScenario,
  getPerformanceThreshold,
  isTabletDevice,
  hasCapability
};