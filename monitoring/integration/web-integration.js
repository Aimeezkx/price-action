// Web platform monitoring integration
// This file should be imported in the main frontend application

import { monitoring } from '../frontend/src/lib/monitoring';

class WebMonitoringIntegration {
  constructor() {
    this.setupErrorTracking();
    this.setupPerformanceTracking();
    this.setupUserInteractionTracking();
    this.setupABTestingIntegration();
  }

  setupErrorTracking() {
    // Global error handler
    window.addEventListener('error', (event) => {
      monitoring.trackEvent('javascript_error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      });
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      monitoring.trackEvent('unhandled_promise_rejection', {
        reason: event.reason?.toString(),
        stack: event.reason?.stack
      });
    });

    // React error boundary integration
    window.reportReactError = (error, errorInfo) => {
      monitoring.trackEvent('react_error', {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    };
  }

  setupPerformanceTracking() {
    // Track route changes
    let currentPath = window.location.pathname;
    const trackRouteChange = () => {
      const newPath = window.location.pathname;
      if (newPath !== currentPath) {
        monitoring.trackEvent('route_change', {
          from: currentPath,
          to: newPath
        });
        currentPath = newPath;
      }
    };

    // Listen for history changes
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      trackRouteChange();
    };

    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      trackRouteChange();
    };

    window.addEventListener('popstate', trackRouteChange);

    // Track API calls
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
      const startTime = performance.now();
      const url = args[0];
      const options = args[1] || {};
      
      try {
        const response = await originalFetch.apply(this, args);
        const duration = performance.now() - startTime;
        
        monitoring.trackAPICall(
          url.toString(),
          options.method || 'GET',
          duration,
          response.status
        );
        
        return response;
      } catch (error) {
        const duration = performance.now() - startTime;
        monitoring.trackAPICall(
          url.toString(),
          options.method || 'GET',
          duration,
          0
        );
        throw error;
      }
    };
  }

  setupUserInteractionTracking() {
    // Track button clicks
    document.addEventListener('click', (event) => {
      const target = event.target;
      if (target.tagName === 'BUTTON' || target.closest('button')) {
        const button = target.tagName === 'BUTTON' ? target : target.closest('button');
        monitoring.trackEvent('button_click', {
          text: button.textContent?.trim(),
          id: button.id,
          className: button.className
        });
      }
    });

    // Track form submissions
    document.addEventListener('submit', (event) => {
      const form = event.target;
      monitoring.trackEvent('form_submit', {
        id: form.id,
        action: form.action,
        method: form.method
      });
    });

    // Track search queries
    document.addEventListener('input', (event) => {
      const target = event.target;
      if (target.type === 'search' || target.placeholder?.toLowerCase().includes('search')) {
        // Debounce search tracking
        clearTimeout(target.searchTimeout);
        target.searchTimeout = setTimeout(() => {
          if (target.value.length > 2) {
            monitoring.trackEvent('search_query', {
              query: target.value,
              field: target.name || target.id
            });
          }
        }, 1000);
      }
    });
  }

  setupABTestingIntegration() {
    // A/B test helper functions
    window.getABTestVariant = async (testName) => {
      return await monitoring.getABTestAssignment(testName);
    };

    window.trackABTestConversion = async (testName, conversionType = 'conversion') => {
      await monitoring.trackABTestEvent(testName, conversionType);
    };

    // Auto-track page views for A/B tests
    const trackPageViewForTests = async () => {
      const activeTests = ['homepage_layout', 'flashcard_design', 'upload_flow'];
      
      for (const testName of activeTests) {
        const assignment = await monitoring.getABTestAssignment(testName);
        if (assignment) {
          await monitoring.trackABTestEvent(testName, 'page_view', {
            path: window.location.pathname
          });
        }
      }
    };

    // Track page views on route changes
    let lastPath = window.location.pathname;
    const checkRouteChange = () => {
      if (window.location.pathname !== lastPath) {
        lastPath = window.location.pathname;
        trackPageViewForTests();
      }
    };

    setInterval(checkRouteChange, 1000);
    trackPageViewForTests(); // Initial page view
  }

  // Feature usage tracking
  trackFeatureUsage(featureName, action = 'use', metadata = {}) {
    monitoring.trackEvent('feature_usage', {
      feature: featureName,
      action,
      ...metadata
    });
  }

  // Document processing tracking
  trackDocumentProcessing(documentId, stage, status, metadata = {}) {
    monitoring.trackEvent('document_processing', {
      documentId,
      stage,
      status,
      ...metadata
    });
  }

  // Study session tracking
  trackStudySession(action, metadata = {}) {
    monitoring.trackEvent('study_session', {
      action,
      ...metadata
    });
  }

  // Feedback submission
  async submitFeedback(feedbackData) {
    const feedbackId = await monitoring.submitFeedback(feedbackData);
    
    if (feedbackId) {
      monitoring.trackEvent('feedback_submitted', {
        feedbackId,
        type: feedbackData.feedbackType
      });
    }
    
    return feedbackId;
  }
}

// Initialize monitoring integration
const webMonitoring = new WebMonitoringIntegration();

// Export for use in React components
export { webMonitoring };

// Global functions for easy access
window.trackFeature = webMonitoring.trackFeatureUsage.bind(webMonitoring);
window.trackDocument = webMonitoring.trackDocumentProcessing.bind(webMonitoring);
window.trackStudy = webMonitoring.trackStudySession.bind(webMonitoring);
window.submitFeedback = webMonitoring.submitFeedback.bind(webMonitoring);