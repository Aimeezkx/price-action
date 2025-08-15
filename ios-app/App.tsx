import React, { useEffect, useState } from 'react';
import { StatusBar, Platform, View, Text, ActivityIndicator } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppNavigator } from './src/navigation/AppNavigator';
import { iOSIntegrationService } from './src/services/iOSIntegrationService';
import { optimizationCoordinator } from './src/services/optimizationCoordinator';
import { performanceMonitoringService } from './src/services/performanceMonitoringService';
import { accessibilityService } from './src/services/accessibilityService';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Loading component with accessibility support
const LoadingScreen = () => {
  const accessibilityProps = accessibilityService.getAccessibilityProps('app_loading', {
    hint: 'The app is starting up and optimizing performance',
  });

  return (
    <View style={{ 
      flex: 1, 
      justifyContent: 'center', 
      alignItems: 'center', 
      backgroundColor: '#FFFFFF' 
    }}>
      <ActivityIndicator size="large" color="#007AFF" />
      <Text 
        style={{ 
          marginTop: 16, 
          fontSize: 16, 
          color: '#333333',
          textAlign: 'center' 
        }}
        {...accessibilityProps}
      >
        Optimizing performance...
      </Text>
    </View>
  );
};

export default function App() {
  const [isOptimizationReady, setIsOptimizationReady] = useState(false);
  const [initializationError, setInitializationError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const initializeApp = async () => {
      try {
        console.log('Starting app initialization with performance optimizations...');
        
        // Track app initialization performance
        const initStartTime = Date.now();
        
        // Initialize iOS-specific features first
        if (Platform.OS === 'ios') {
          await iOSIntegrationService.initialize({
            notifications: true,
            widgets: true,
            siriShortcuts: true,
            hapticFeedback: true,
            offlineMode: true,
          });
        }
        
        // Initialize all optimization services
        await optimizationCoordinator.initializeOptimizations();
        
        // Track initialization completion
        performanceMonitoringService.trackScreenTransition('app_init', initStartTime);
        
        // Announce successful initialization for accessibility
        accessibilityService.announceForAccessibility('Document Learning App loaded and optimized');
        
        if (mounted) {
          setIsOptimizationReady(true);
          console.log(`App initialization completed in ${Date.now() - initStartTime}ms`);
        }
        
      } catch (error) {
        console.error('Failed to initialize app optimizations:', error);
        
        if (mounted) {
          setInitializationError(error instanceof Error ? error.message : 'Unknown initialization error');
          // Continue with app loading even if optimizations fail
          setIsOptimizationReady(true);
        }
      }
    };

    initializeApp();

    // Cleanup function
    return () => {
      mounted = false;
      
      // Cleanup services
      const cleanup = async () => {
        try {
          await optimizationCoordinator.shutdown();
          
          if (Platform.OS === 'ios') {
            iOSIntegrationService.cleanup();
          }
        } catch (error) {
          console.error('Failed to cleanup services:', error);
        }
      };
      
      cleanup();
    };
  }, []);

  // Show loading screen while optimizations are initializing
  if (!isOptimizationReady) {
    return <LoadingScreen />;
  }

  // Show error message if initialization failed but continue with app
  if (initializationError) {
    console.warn('App started with optimization errors:', initializationError);
    // Could show a toast or banner here, but continue with normal app flow
  }

  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <AppNavigator />
    </QueryClientProvider>
  );
}