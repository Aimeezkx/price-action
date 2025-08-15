// iOS platform monitoring integration
// This file should be imported in the main iOS application

import { monitoring } from '../ios-app/src/services/monitoringService';
import { AppState, AppStateStatus } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';

class iOSMonitoringIntegration {
  private appLaunchTime: number;
  private currentScreen: string = '';
  private sessionStartTime: number;

  constructor() {
    this.appLaunchTime = Date.now();
    this.sessionStartTime = Date.now();
    this.setupAppStateTracking();
    this.setupNavigationTracking();
    this.setupErrorTracking();
    this.setupPerformanceTracking();
  }

  setupAppStateTracking() {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      if (nextAppState === 'active') {
        // App became active
        monitoring.trackEvent('app_foreground', {
          timestamp: Date.now()
        });
        
        // Track app launch time on first activation
        if (this.appLaunchTime) {
          const launchDuration = Date.now() - this.appLaunchTime;
          monitoring.trackAppLaunch(launchDuration);
          this.appLaunchTime = 0; // Reset so we don't track again
        }
      } else if (nextAppState === 'background') {
        // App went to background
        const sessionDuration = Date.now() - this.sessionStartTime;
        monitoring.trackEvent('app_background', {
          sessionDuration,
          timestamp: Date.now()
        });
      } else if (nextAppState === 'inactive') {
        // App became inactive (e.g., phone call, notification)
        monitoring.trackEvent('app_inactive', {
          timestamp: Date.now()
        });
      }
    });
  }

  setupNavigationTracking() {
    // Navigation state change listener
    const onNavigationStateChange = (prevState: any, currentState: any) => {
      const prevScreen = this.getActiveRouteName(prevState);
      const currentScreen = this.getActiveRouteName(currentState);
      
      if (prevScreen !== currentScreen) {
        const transitionTime = Date.now();
        
        // Track screen transition
        monitoring.trackScreenTransition(
          prevScreen || 'unknown',
          currentScreen || 'unknown',
          transitionTime - (this.lastNavigationTime || transitionTime)
        );
        
        // Track screen view
        monitoring.trackEvent('screen_view', {
          screen: currentScreen,
          previousScreen: prevScreen,
          timestamp: transitionTime
        });
        
        this.currentScreen = currentScreen || '';
        this.lastNavigationTime = transitionTime;
      }
    };

    // Export for use in NavigationContainer
    this.onNavigationStateChange = onNavigationStateChange;
  }

  private lastNavigationTime?: number;

  private getActiveRouteName(navigationState: any): string | undefined {
    if (!navigationState) return undefined;
    
    const route = navigationState.routes[navigationState.index];
    
    if (route.state) {
      return this.getActiveRouteName(route.state);
    }
    
    return route.name;
  }

  setupErrorTracking() {
    // Global error handler
    const originalConsoleError = console.error;
    console.error = (...args) => {
      // Track console errors
      monitoring.trackEvent('console_error', {
        message: args.join(' '),
        timestamp: Date.now()
      });
      
      originalConsoleError.apply(console, args);
    };

    // React Native error handler
    const originalHandler = global.ErrorUtils?.getGlobalHandler();
    global.ErrorUtils?.setGlobalHandler((error: Error, isFatal: boolean) => {
      monitoring.trackCrash(error, {
        isFatal,
        screen: this.currentScreen,
        timestamp: Date.now()
      });
      
      // Call original handler
      if (originalHandler) {
        originalHandler(error, isFatal);
      }
    });
  }

  setupPerformanceTracking() {
    // Memory monitoring
    setInterval(() => {
      // Note: React Native doesn't have direct memory access
      // This would need to be implemented with native modules
      // For now, we'll track JavaScript heap if available
      if (global.performance && (global.performance as any).memory) {
        const memory = (global.performance as any).memory;
        monitoring.trackMemoryUsage(memory.usedJSHeapSize);
      }
    }, 60000); // Every minute

    // Battery monitoring (would need native module)
    // This is a placeholder for battery monitoring integration
    setInterval(() => {
      // getBatteryLevel() would be implemented in native module
      // monitoring.trackBatteryDrain(batteryDrainRate);
    }, 300000); // Every 5 minutes
  }

  // Feature usage tracking
  trackFeatureUsage(featureName: string, action: string = 'use', metadata: any = {}) {
    monitoring.trackEvent('feature_usage', {
      feature: featureName,
      action,
      platform: 'ios',
      screen: this.currentScreen,
      ...metadata
    });
  }

  // Document processing tracking
  trackDocumentProcessing(documentId: string, stage: string, status: string, metadata: any = {}) {
    monitoring.trackEvent('document_processing', {
      documentId,
      stage,
      status,
      platform: 'ios',
      ...metadata
    });
  }

  // Study session tracking
  trackStudySession(action: string, metadata: any = {}) {
    monitoring.trackEvent('study_session', {
      action,
      platform: 'ios',
      screen: this.currentScreen,
      ...metadata
    });
  }

  // Flashcard interaction tracking
  trackFlashcardInteraction(cardId: string, action: string, metadata: any = {}) {
    monitoring.trackEvent('flashcard_interaction', {
      cardId,
      action,
      platform: 'ios',
      ...metadata
    });
  }

  // Search tracking
  trackSearch(query: string, results: number, metadata: any = {}) {
    monitoring.trackEvent('search', {
      query,
      results,
      platform: 'ios',
      screen: this.currentScreen,
      ...metadata
    });
  }

  // Feedback submission
  async submitFeedback(feedbackData: any) {
    const feedbackId = await monitoring.submitFeedback({
      ...feedbackData,
      metadata: {
        ...feedbackData.metadata,
        screen: this.currentScreen,
        appVersion: '1.0.0' // This should come from app config
      }
    });
    
    if (feedbackId) {
      monitoring.trackEvent('feedback_submitted', {
        feedbackId,
        type: feedbackData.feedbackType,
        platform: 'ios'
      });
    }
    
    return feedbackId;
  }

  // A/B testing integration
  async getABTestVariant(testName: string) {
    return await monitoring.getABTestAssignment(testName);
  }

  async trackABTestConversion(testName: string, conversionType: string = 'conversion') {
    await monitoring.trackABTestEvent(testName, conversionType, {
      screen: this.currentScreen,
      platform: 'ios'
    });
  }

  // Performance metrics
  recordCustomMetric(metricName: string, value: number, unit?: string, metadata?: any) {
    monitoring.recordMetric({
      metricType: 'custom',
      metricName,
      value,
      unit,
      metadata: {
        ...metadata,
        screen: this.currentScreen,
        platform: 'ios'
      }
    });
  }

  // Gesture tracking
  trackGesture(gestureType: string, target: string, metadata: any = {}) {
    monitoring.trackEvent('gesture', {
      gestureType,
      target,
      platform: 'ios',
      screen: this.currentScreen,
      ...metadata
    });
  }

  // Network request tracking
  trackNetworkRequest(url: string, method: string, duration: number, status: number, size?: number) {
    monitoring.recordMetric({
      metricType: 'network',
      metricName: 'api_response_time',
      value: duration,
      unit: 'ms',
      metadata: {
        url,
        method,
        status,
        size,
        platform: 'ios'
      }
    });
  }

  // Export navigation handler for NavigationContainer
  onNavigationStateChange: (prevState: any, currentState: any) => void;
}

// Initialize monitoring integration
const iOSMonitoring = new iOSMonitoringIntegration();

// Export for use in React Native components
export { iOSMonitoring };

// Navigation container wrapper with monitoring
export const MonitoredNavigationContainer = ({ children, ...props }: any) => {
  return (
    <NavigationContainer
      {...props}
      onStateChange={iOSMonitoring.onNavigationStateChange}
    >
      {children}
    </NavigationContainer>
  );
};

// Hook for easy access to monitoring functions
export const useMonitoring = () => {
  return {
    trackFeature: iOSMonitoring.trackFeatureUsage.bind(iOSMonitoring),
    trackDocument: iOSMonitoring.trackDocumentProcessing.bind(iOSMonitoring),
    trackStudy: iOSMonitoring.trackStudySession.bind(iOSMonitoring),
    trackFlashcard: iOSMonitoring.trackFlashcardInteraction.bind(iOSMonitoring),
    trackSearch: iOSMonitoring.trackSearch.bind(iOSMonitoring),
    submitFeedback: iOSMonitoring.submitFeedback.bind(iOSMonitoring),
    getABTestVariant: iOSMonitoring.getABTestVariant.bind(iOSMonitoring),
    trackABTestConversion: iOSMonitoring.trackABTestConversion.bind(iOSMonitoring),
    recordMetric: iOSMonitoring.recordCustomMetric.bind(iOSMonitoring),
    trackGesture: iOSMonitoring.trackGesture.bind(iOSMonitoring),
    trackNetwork: iOSMonitoring.trackNetworkRequest.bind(iOSMonitoring)
  };
};