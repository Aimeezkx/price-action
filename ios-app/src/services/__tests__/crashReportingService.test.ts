import { crashReportingService } from '../crashReportingService';

// Mock Firebase Crashlytics
jest.mock('@react-native-firebase/crashlytics', () => ({
  __esModule: true,
  default: () => ({
    setCrashlyticsCollectionEnabled: jest.fn(() => Promise.resolve()),
    setUserId: jest.fn(),
    setCustomKey: jest.fn(),
    recordError: jest.fn(),
    log: jest.fn(),
    crash: jest.fn(),
  }),
}));

// Mock Firebase Analytics
jest.mock('@react-native-firebase/analytics', () => ({
  __esModule: true,
  default: () => ({
    setUserId: jest.fn(),
    setUserProperty: jest.fn(),
    logEvent: jest.fn(),
  }),
}));

// Mock Bugsnag
jest.mock('@bugsnag/react-native', () => ({
  start: jest.fn(),
  setUser: jest.fn(),
  notify: jest.fn(),
  leaveBreadcrumb: jest.fn(),
}));

// Mock exception handlers
jest.mock('react-native-exception-handler', () => ({
  setJSExceptionHandler: jest.fn(),
  setNativeExceptionHandler: jest.fn(),
}));

describe('CrashReportingService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      await crashReportingService.initialize();
      
      // Verify that all services were initialized
      expect(require('@react-native-firebase/crashlytics').default().setCrashlyticsCollectionEnabled)
        .toHaveBeenCalledWith(true);
      expect(require('@bugsnag/react-native').start).toHaveBeenCalled();
    });

    it('should handle initialization errors gracefully', async () => {
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      crashlytics.setCrashlyticsCollectionEnabled.mockRejectedValueOnce(new Error('Init failed'));

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await crashReportingService.initialize();
      
      expect(consoleSpy).toHaveBeenCalledWith('Failed to initialize crash reporting:', expect.any(Error));
      consoleSpy.mockRestore();
    });

    it('should not initialize twice', async () => {
      await crashReportingService.initialize();
      await crashReportingService.initialize();
      
      // Should only be called once
      expect(require('@react-native-firebase/crashlytics').default().setCrashlyticsCollectionEnabled)
        .toHaveBeenCalledTimes(1);
    });
  });

  describe('User Management', () => {
    beforeEach(async () => {
      await crashReportingService.initialize();
    });

    it('should set user ID correctly', () => {
      const userId = 'test-user-123';
      crashReportingService.setUserId(userId);
      
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      const analytics = require('@react-native-firebase/analytics').default();
      const Bugsnag = require('@bugsnag/react-native');
      
      expect(crashlytics.setUserId).toHaveBeenCalledWith(userId);
      expect(analytics.setUserId).toHaveBeenCalledWith(userId);
      expect(Bugsnag.setUser).toHaveBeenCalledWith(userId);
    });

    it('should set user properties correctly', () => {
      const properties = {
        plan: 'premium',
        region: 'us-east',
      };
      
      crashReportingService.setUserProperties(properties);
      
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      const analytics = require('@react-native-firebase/analytics').default();
      
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('plan', 'premium');
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('region', 'us-east');
      expect(analytics.setUserProperty).toHaveBeenCalledWith('plan', 'premium');
      expect(analytics.setUserProperty).toHaveBeenCalledWith('region', 'us-east');
    });
  });

  describe('Error Reporting', () => {
    beforeEach(async () => {
      await crashReportingService.initialize();
    });

    it('should record errors with context', () => {
      const error = new Error('Test error');
      const context = {
        screen: 'StudyScreen',
        action: 'flip_card',
        cardId: 'card-123',
      };
      
      crashReportingService.recordError(error, context);
      
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      const analytics = require('@react-native-firebase/analytics').default();
      const Bugsnag = require('@bugsnag/react-native');
      
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('screen', 'StudyScreen');
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('action', 'flip_card');
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('cardId', 'card-123');
      expect(crashlytics.recordError).toHaveBeenCalledWith(error);
      
      expect(Bugsnag.notify).toHaveBeenCalledWith(error, expect.any(Function));
      expect(analytics.logEvent).toHaveBeenCalledWith('app_error', expect.objectContaining({
        error_message: 'Test error',
        screen: 'StudyScreen',
        action: 'flip_card',
      }));
    });

    it('should record warnings', () => {
      const message = 'Test warning';
      const context = { screen: 'SearchScreen' };
      
      crashReportingService.recordWarning(message, context);
      
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      const Bugsnag = require('@bugsnag/react-native');
      
      expect(crashlytics.log).toHaveBeenCalledWith(message);
      expect(Bugsnag.notify).toHaveBeenCalledWith(expect.any(Error), expect.any(Function));
    });

    it('should handle reporting errors gracefully', () => {
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      crashlytics.recordError.mockImplementationOnce(() => {
        throw new Error('Reporting failed');
      });

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      const error = new Error('Test error');
      crashReportingService.recordError(error);
      
      expect(consoleSpy).toHaveBeenCalledWith('Failed to record error:', expect.any(Error));
      consoleSpy.mockRestore();
    });
  });

  describe('Performance Monitoring', () => {
    beforeEach(async () => {
      await crashReportingService.initialize();
    });

    it('should record performance metrics', () => {
      const metrics = {
        renderTime: 150,
        animationDuration: 300,
        memoryUsage: 45.5,
      };
      const context = { screen: 'StudyScreen' };
      
      crashReportingService.recordPerformanceMetrics(metrics, context);
      
      const analytics = require('@react-native-firebase/analytics').default();
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      
      expect(analytics.logEvent).toHaveBeenCalledWith('performance_metrics', {
        render_time: 150,
        animation_duration: 300,
        api_response_time: undefined,
        memory_usage: 45.5,
        battery_level: undefined,
        screen: 'StudyScreen',
      });
      
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('last_render_time', 150);
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('memory_usage', 45.5);
    });

    it('should record user actions', () => {
      const action = 'grade_card';
      const context = {
        screen: 'StudyScreen',
        cardId: 'card-123',
      };
      
      crashReportingService.recordUserAction(action, context);
      
      const analytics = require('@react-native-firebase/analytics').default();
      const Bugsnag = require('@bugsnag/react-native');
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      
      expect(analytics.logEvent).toHaveBeenCalledWith('user_action', {
        action: 'grade_card',
        screen: 'StudyScreen',
        card_id: 'card-123',
        document_id: undefined,
        search_query: undefined,
      });
      
      expect(Bugsnag.leaveBreadcrumb).toHaveBeenCalledWith('User action: grade_card', {
        type: 'user',
        screen: 'StudyScreen',
        cardId: 'card-123',
      });
      
      expect(crashlytics.log).toHaveBeenCalledWith('User action: grade_card');
    });

    it('should record API calls', () => {
      const endpoint = '/api/cards';
      const method = 'GET';
      const responseTime = 250;
      const success = true;
      
      crashReportingService.recordAPICall(endpoint, method, responseTime, success);
      
      const analytics = require('@react-native-firebase/analytics').default();
      const Bugsnag = require('@bugsnag/react-native');
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      
      expect(analytics.logEvent).toHaveBeenCalledWith('api_call', {
        endpoint: '/api/cards',
        method: 'GET',
        response_time: 250,
        success: true,
      });
      
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('last_api_call', 'GET /api/cards');
      expect(crashlytics.setCustomKey).toHaveBeenCalledWith('last_api_response_time', 250);
      
      expect(Bugsnag.leaveBreadcrumb).toHaveBeenCalledWith('API call: GET /api/cards', {
        type: 'request',
        metadata: {
          responseTime: 250,
          success: true,
        },
      });
    });
  });

  describe('Testing Functions', () => {
    beforeEach(async () => {
      await crashReportingService.initialize();
    });

    it('should test crash reporting', () => {
      crashReportingService.testCrash();
      
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      expect(crashlytics.crash).toHaveBeenCalled();
    });

    it('should test error reporting', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      crashReportingService.testError();
      
      expect(consoleSpy).toHaveBeenCalledWith('Testing error reporting...');
      
      const crashlytics = require('@react-native-firebase/crashlytics').default();
      expect(crashlytics.recordError).toHaveBeenCalledWith(expect.any(Error));
      
      consoleSpy.mockRestore();
    });
  });

  describe('Uninitialized State', () => {
    it('should handle calls before initialization gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      const error = new Error('Test error');
      crashReportingService.recordError(error);
      
      expect(consoleSpy).toHaveBeenCalledWith('Crash reporting not initialized:', error);
      consoleSpy.mockRestore();
    });

    it('should not crash when calling methods before initialization', () => {
      expect(() => {
        crashReportingService.setUserId('test-user');
        crashReportingService.recordWarning('test warning');
        crashReportingService.recordPerformanceMetrics({ renderTime: 100 });
        crashReportingService.recordUserAction('test action');
        crashReportingService.recordAPICall('/test', 'GET', 100, true);
      }).not.toThrow();
    });
  });
});