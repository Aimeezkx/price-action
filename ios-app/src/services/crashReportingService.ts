import crashlytics from '@react-native-firebase/crashlytics';
import analytics from '@react-native-firebase/analytics';
import Bugsnag from '@bugsnag/react-native';
import { setJSExceptionHandler, setNativeExceptionHandler } from 'react-native-exception-handler';

export interface ErrorContext {
  userId?: string;
  screen?: string;
  action?: string;
  cardId?: string;
  documentId?: string;
  searchQuery?: string;
  [key: string]: any;
}

export interface PerformanceMetrics {
  renderTime?: number;
  animationDuration?: number;
  apiResponseTime?: number;
  memoryUsage?: number;
  batteryLevel?: number;
}

class CrashReportingService {
  private isInitialized = false;
  private userId: string | null = null;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Initialize Firebase Crashlytics
      await crashlytics().setCrashlyticsCollectionEnabled(true);
      
      // Initialize Bugsnag
      Bugsnag.start();
      
      // Set up global error handlers
      this.setupGlobalErrorHandlers();
      
      // Set up performance monitoring
      this.setupPerformanceMonitoring();
      
      this.isInitialized = true;
      console.log('Crash reporting service initialized');
    } catch (error) {
      console.error('Failed to initialize crash reporting:', error);
    }
  }

  setUserId(userId: string): void {
    this.userId = userId;
    
    if (this.isInitialized) {
      crashlytics().setUserId(userId);
      Bugsnag.setUser(userId);
      analytics().setUserId(userId);
    }
  }

  setUserProperties(properties: Record<string, string>): void {
    if (!this.isInitialized) return;

    Object.entries(properties).forEach(([key, value]) => {
      crashlytics().setCustomKey(key, value);
      analytics().setUserProperty(key, value);
    });

    Bugsnag.setUser(this.userId || 'anonymous', undefined, properties);
  }

  recordError(error: Error, context?: ErrorContext): void {
    if (!this.isInitialized) {
      console.error('Crash reporting not initialized:', error);
      return;
    }

    try {
      // Add context to error
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          crashlytics().setCustomKey(key, String(value));
        });
      }

      // Record to Firebase Crashlytics
      crashlytics().recordError(error);

      // Record to Bugsnag with context
      Bugsnag.notify(error, (event) => {
        if (context) {
          event.addMetadata('context', context);
        }
        event.severity = 'error';
      });

      // Log analytics event
      analytics().logEvent('app_error', {
        error_message: error.message,
        error_stack: error.stack?.substring(0, 500),
        screen: context?.screen,
        action: context?.action,
      });

      console.error('Error recorded:', error.message, context);
    } catch (reportingError) {
      console.error('Failed to record error:', reportingError);
    }
  }

  recordWarning(message: string, context?: ErrorContext): void {
    if (!this.isInitialized) return;

    try {
      const warning = new Error(message);
      
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          crashlytics().setCustomKey(key, String(value));
        });
      }

      // Record as non-fatal error
      crashlytics().log(message);

      // Record to Bugsnag as warning
      Bugsnag.notify(warning, (event) => {
        if (context) {
          event.addMetadata('context', context);
        }
        event.severity = 'warning';
      });

      console.warn('Warning recorded:', message, context);
    } catch (error) {
      console.error('Failed to record warning:', error);
    }
  }

  recordPerformanceMetrics(metrics: PerformanceMetrics, context?: ErrorContext): void {
    if (!this.isInitialized) return;

    try {
      // Log performance metrics
      analytics().logEvent('performance_metrics', {
        render_time: metrics.renderTime,
        animation_duration: metrics.animationDuration,
        api_response_time: metrics.apiResponseTime,
        memory_usage: metrics.memoryUsage,
        battery_level: metrics.batteryLevel,
        screen: context?.screen,
      });

      // Set custom keys for crash context
      if (metrics.renderTime) {
        crashlytics().setCustomKey('last_render_time', metrics.renderTime);
      }
      if (metrics.memoryUsage) {
        crashlytics().setCustomKey('memory_usage', metrics.memoryUsage);
      }

      console.log('Performance metrics recorded:', metrics);
    } catch (error) {
      console.error('Failed to record performance metrics:', error);
    }
  }

  recordUserAction(action: string, context?: ErrorContext): void {
    if (!this.isInitialized) return;

    try {
      analytics().logEvent('user_action', {
        action,
        screen: context?.screen,
        card_id: context?.cardId,
        document_id: context?.documentId,
        search_query: context?.searchQuery,
      });

      // Add breadcrumb for crash context
      Bugsnag.leaveBreadcrumb(`User action: ${action}`, {
        type: 'user',
        ...context,
      });

      crashlytics().log(`User action: ${action}`);
    } catch (error) {
      console.error('Failed to record user action:', error);
    }
  }

  recordAPICall(endpoint: string, method: string, responseTime: number, success: boolean): void {
    if (!this.isInitialized) return;

    try {
      analytics().logEvent('api_call', {
        endpoint,
        method,
        response_time: responseTime,
        success,
      });

      crashlytics().setCustomKey('last_api_call', `${method} ${endpoint}`);
      crashlytics().setCustomKey('last_api_response_time', responseTime);

      Bugsnag.leaveBreadcrumb(`API call: ${method} ${endpoint}`, {
        type: 'request',
        metadata: {
          responseTime,
          success,
        },
      });
    } catch (error) {
      console.error('Failed to record API call:', error);
    }
  }

  private setupGlobalErrorHandlers(): void {
    // Handle JavaScript exceptions
    setJSExceptionHandler((error, isFatal) => {
      console.error('JS Exception:', error, 'Fatal:', isFatal);
      
      this.recordError(error, {
        screen: 'unknown',
        action: 'js_exception',
        fatal: isFatal.toString(),
      });

      if (isFatal) {
        // Show user-friendly error message
        // In a real app, you might show a modal or navigate to an error screen
        console.log('Fatal error occurred, app may crash');
      }
    }, true);

    // Handle native exceptions
    setNativeExceptionHandler((exceptionString) => {
      console.error('Native Exception:', exceptionString);
      
      const error = new Error(`Native Exception: ${exceptionString}`);
      this.recordError(error, {
        screen: 'unknown',
        action: 'native_exception',
        fatal: 'true',
      });
    });

    // Handle unhandled promise rejections
    const originalHandler = global.ErrorUtils?.getGlobalHandler();
    global.ErrorUtils?.setGlobalHandler((error, isFatal) => {
      console.error('Unhandled Promise Rejection:', error);
      
      this.recordError(error, {
        screen: 'unknown',
        action: 'unhandled_promise_rejection',
        fatal: isFatal?.toString() || 'false',
      });

      // Call original handler
      originalHandler?.(error, isFatal);
    });
  }

  private setupPerformanceMonitoring(): void {
    // Monitor memory usage periodically
    setInterval(() => {
      if (global.performance?.memory) {
        const memoryUsage = global.performance.memory.usedJSHeapSize;
        
        // Record if memory usage is high (>50MB)
        if (memoryUsage > 50 * 1024 * 1024) {
          this.recordPerformanceMetrics({
            memoryUsage: memoryUsage / (1024 * 1024), // Convert to MB
          });
        }
      }
    }, 30000); // Check every 30 seconds

    // Monitor long tasks
    if (global.performance?.mark && global.performance?.measure) {
      const originalMark = global.performance.mark;
      global.performance.mark = function(markName: string) {
        const result = originalMark.call(this, markName);
        
        // Record performance marks for crash context
        crashReportingService.recordUserAction('performance_mark', {
          action: markName,
        });
        
        return result;
      };
    }
  }

  testCrash(): void {
    if (!this.isInitialized) return;
    
    console.log('Testing crash reporting...');
    crashlytics().crash();
  }

  testError(): void {
    if (!this.isInitialized) return;
    
    console.log('Testing error reporting...');
    const testError = new Error('Test error for crash reporting');
    this.recordError(testError, {
      screen: 'test',
      action: 'test_error',
    });
  }
}

export const crashReportingService = new CrashReportingService();