module.exports = {
  testRunner: {
    args: {
      '$0': 'jest',
      config: 'e2e/jest.config.js'
    },
    jest: {
      setupFilesAfterEnv: ['<rootDir>/e2e/init.js']
    }
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/DocumentLearningIOS.app',
      build: 'xcodebuild -workspace ios/DocumentLearningIOS.xcworkspace -scheme DocumentLearningIOS -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build'
    },
    'ios.release': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Release-iphonesimulator/DocumentLearningIOS.app',
      build: 'xcodebuild -workspace ios/DocumentLearningIOS.xcworkspace -scheme DocumentLearningIOS -configuration Release -sdk iphonesimulator -derivedDataPath ios/build'
    }
  },
  devices: {
    simulator: {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 14'
      }
    },
    'iphone-se': {
      type: 'ios.simulator',
      device: {
        type: 'iPhone SE (3rd generation)'
      }
    },
    'iphone-14-pro': {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 14 Pro'
      }
    },
    'iphone-14-pro-max': {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 14 Pro Max'
      }
    },
    'ipad-air': {
      type: 'ios.simulator',
      device: {
        type: 'iPad Air (5th generation)'
      }
    },
    'ipad-pro-11': {
      type: 'ios.simulator',
      device: {
        type: 'iPad Pro (11-inch) (4th generation)'
      }
    },
    'ipad-pro-12-9': {
      type: 'ios.simulator',
      device: {
        type: 'iPad Pro (12.9-inch) (6th generation)'
      }
    }
  },
  configurations: {
    'ios.sim.debug': {
      device: 'simulator',
      app: 'ios.debug'
    },
    'ios.sim.release': {
      device: 'simulator',
      app: 'ios.release'
    },
    'cross-platform.iphone-se': {
      device: 'iphone-se',
      app: 'ios.debug'
    },
    'cross-platform.iphone-14-pro': {
      device: 'iphone-14-pro',
      app: 'ios.debug'
    },
    'cross-platform.iphone-14-pro-max': {
      device: 'iphone-14-pro-max',
      app: 'ios.debug'
    },
    'cross-platform.ipad-air': {
      device: 'ipad-air',
      app: 'ios.debug'
    },
    'cross-platform.ipad-pro-11': {
      device: 'ipad-pro-11',
      app: 'ios.debug'
    },
    'cross-platform.ipad-pro-12-9': {
      device: 'ipad-pro-12-9',
      app: 'ios.debug'
    }
  }
};