import { AppState, AppStateStatus } from 'react-native';
import { imageCacheService } from './imageCacheService';
import { backgroundSyncService } from './backgroundSyncService';
import { memoryOptimizationService } from './memoryOptimizationService';
import { batteryOptimizationService } from './batteryOptimizationService';
import { accessibilityService } from './accessibilityService';
import { performanceMonitoringService } from './performanceMonitoringService';

export interface OptimizationStatus {
  imageCacheEnabled: boolean;
  backgroundSyncEnabled: boolean;
  memoryOptimizationEnabled: boolean;
  batteryOptimizationEnabled: boolean;
  accessibilityEnabled: boolean;
  performanceMonitoringEnabled: boolean;
  overallHealth: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface OptimizationConfig {
  enableImageCache: boolean;
  enableBackgroundSync: boolean;
  enableMemoryOptimization: boolean;
  enableBatteryOptimization: boolean;
  enableAccessibility: boolean;
  enablePerformanceMonitoring: boolean;
  autoOptimization: boolean;
}

class OptimizationCoordinator {
  private readonly DEFAULT_CONFIG: OptimizationConfig = {
    enableImageCache: true,
    enableBackgroundSync: true,
    enableMemoryOptimization: true,
    enableBatteryOptimization: true,
    enableAccessibility: true,
    enablePerformanceMonitoring: true,
    autoOptimization: true,
  };

  private config: OptimizationConfig;
  private isInitialized = false;
  private appState: AppStateStatus = 'active';
  private statusListeners: ((status: OptimizationStatus) => void)[] = [];

  constructor(config?: Partial<OptimizationConfig>) {
    this.config = { ...this.DEFAULT_CONFIG, ...config };
    this.initializeAppStateListener();
  }

  private initializeAppStateListener(): void {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      this.appState = nextAppState;

      if (nextAppState === 'background') {
        this.handleAppBackground();
      } else if (nextAppState === 'active') {
        this.handleAppForeground();
      }
    });
  }

  async initializeOptimizations(): Promise<void> {
    if (this.isInitialized) {
      console.log('Optimization services already initialized');
      return;
    }

    console.log('Initializing iOS performance and UX optimizations...');

    try {
      const initPromises: Promise<void>[] = [];

      // Initialize image caching
      if (this.config.enableImageCache) {
        console.log('Initializing image cache service...');
        initPromises.push(imageCacheService.initialize());
      }

      // Initialize background sync
      if (this.config.enableBackgroundSync) {
        console.log('Initializing background sync service...');
        initPromises.push(backgroundSyncService.startBackgroundSync());
      }

      // Initialize memory optimization
      if (this.config.enableMemoryOptimization) {
        console.log('Initializing memory optimization service...');
        initPromises.push(memoryOptimizationService.startMemoryOptimization());
      }

      // Initialize battery optimization
      if (this.config.enableBatteryOptimization) {
        console.log('Initializing battery optimization service...');
        initPromises.push(batteryOptimizationService.startBatteryOptimization());
      }

      // Initialize accessibility
      if (this.config.enableAccessibility) {
        console.log('Initializing accessibility service...');
        initPromises.push(accessibilityService.initializeAccessibility());
      }

      // Initialize performance monitoring
      if (this.config.enablePerformanceMonitoring) {
        console.log('Initializing performance monitoring service...');
        initPromises.push(performanceMonitoringService.startPerformanceMonitoring());
      }

      // Wait for all services to initialize
      await Promise.all(initPromises);

      // Set up cross-service coordination
      this.setupServiceCoordination();

      this.isInitialized = true;
      console.log('All optimization services initialized successfully');

      // Notify listeners
      this.notifyStatusListeners();

    } catch (error) {
      console.error('Failed to initialize optimization services:', error);
      throw error;
    }
  }

  private setupServiceCoordination(): void {
    // Set up memory warning coordination
    memoryOptimizationService.onMemoryWarning(() => {
      console.log('Memory warning received - coordinating optimizations');
      this.handleMemoryWarning();
    });

    // Set up battery optimization coordination
    batteryOptimizationService.addBatteryStatsListener((stats) => {
      if (stats.batteryLevel < 20 && !stats.powerSaveModeActive) {
        console.log('Low battery detected - enabling aggressive optimizations');
        this.handleLowBattery();
      }
    });

    // Set up accessibility coordination
    accessibilityService.addAccessibilityStateListener((state) => {
      if (state.isScreenReaderEnabled || state.isReduceMotionEnabled) {
        console.log('Accessibility features detected - adjusting optimizations');
        this.handleAccessibilityChanges(state);
      }
    });
  }

  private async handleMemoryWarning(): Promise<void> {
    try {
      // Coordinate memory cleanup across services
      await Promise.all([
        imageCacheService.clearCache(),
        memoryOptimizationService.forceCleanup(true),
      ]);

      // Reduce background sync frequency temporarily
      if (this.config.enableBackgroundSync) {
        // This would require extending backgroundSyncService with temporary frequency adjustment
        console.log('Reducing sync frequency due to memory pressure');
      }

    } catch (error) {
      console.error('Failed to handle memory warning:', error);
    }
  }

  private async handleLowBattery(): Promise<void> {
    try {
      // Enable aggressive power saving across all services
      await Promise.all([
        batteryOptimizationService.togglePowerSaveMode(true),
        memoryOptimizationService.forceCleanup(true),
      ]);

      // Reduce image cache size
      imageCacheService.updateConfig({
        maxCacheSize: 25 * 1024 * 1024, // 25MB
        compressionQuality: 0.6,
      });

    } catch (error) {
      console.error('Failed to handle low battery:', error);
    }
  }

  private handleAccessibilityChanges(state: any): void {
    try {
      // Adjust optimizations based on accessibility needs
      if (state.isReduceMotionEnabled) {
        // Disable animations in performance monitoring
        console.log('Reducing animations for accessibility');
      }

      if (state.isScreenReaderEnabled) {
        // Prioritize content loading over visual optimizations
        console.log('Optimizing for screen reader usage');
      }

    } catch (error) {
      console.error('Failed to handle accessibility changes:', error);
    }
  }

  private async handleAppBackground(): Promise<void> {
    console.log('App went to background - applying background optimizations');

    try {
      // Trigger aggressive cleanup when app goes to background
      if (this.config.enableMemoryOptimization) {
        await memoryOptimizationService.performCleanup(true);
      }

      // Reduce sync frequency in background
      // Pause non-essential services

    } catch (error) {
      console.error('Failed to handle app background:', error);
    }
  }

  private async handleAppForeground(): Promise<void> {
    console.log('App came to foreground - resuming normal operations');

    try {
      // Resume normal operations
      // Trigger sync if needed
      if (this.config.enableBackgroundSync) {
        await backgroundSyncService.triggerSync();
      }

      // Update performance metrics
      if (this.config.enablePerformanceMonitoring) {
        performanceMonitoringService.trackScreenTransition('app_foreground');
      }

    } catch (error) {
      console.error('Failed to handle app foreground:', error);
    }
  }

  async getOptimizationStatus(): Promise<OptimizationStatus> {
    try {
      const [
        memoryStats,
        batteryStats,
        syncStatus,
        cacheStats,
        accessibilityState,
        performanceMetrics,
      ] = await Promise.all([
        this.config.enableMemoryOptimization ? memoryOptimizationService.getMemoryStats() : null,
        this.config.enableBatteryOptimization ? batteryOptimizationService.getBatteryStats() : null,
        this.config.enableBackgroundSync ? backgroundSyncService.getSyncStatus() : null,
        this.config.enableImageCache ? imageCacheService.getCacheStats() : null,
        this.config.enableAccessibility ? accessibilityService.getAccessibilityState() : null,
        this.config.enablePerformanceMonitoring ? performanceMonitoringService.getCurrentMetrics() : null,
      ]);

      // Calculate overall health score
      let healthScore = 100;

      if (memoryStats && memoryStats.totalMemoryUsage > 150 * 1024 * 1024) {
        healthScore -= 20; // High memory usage
      }

      if (batteryStats && batteryStats.batteryLevel < 20) {
        healthScore -= 15; // Low battery
      }

      if (syncStatus && syncStatus.pendingChanges > 10) {
        healthScore -= 10; // Many pending changes
      }

      if (performanceMetrics && performanceMetrics.errorCount > 5) {
        healthScore -= 15; // High error rate
      }

      const overallHealth = 
        healthScore >= 90 ? 'excellent' :
        healthScore >= 70 ? 'good' :
        healthScore >= 50 ? 'fair' : 'poor';

      return {
        imageCacheEnabled: this.config.enableImageCache,
        backgroundSyncEnabled: this.config.enableBackgroundSync,
        memoryOptimizationEnabled: this.config.enableMemoryOptimization,
        batteryOptimizationEnabled: this.config.enableBatteryOptimization,
        accessibilityEnabled: this.config.enableAccessibility,
        performanceMonitoringEnabled: this.config.enablePerformanceMonitoring,
        overallHealth,
      };

    } catch (error) {
      console.error('Failed to get optimization status:', error);
      return {
        imageCacheEnabled: false,
        backgroundSyncEnabled: false,
        memoryOptimizationEnabled: false,
        batteryOptimizationEnabled: false,
        accessibilityEnabled: false,
        performanceMonitoringEnabled: false,
        overallHealth: 'poor',
      };
    }
  }

  async performFullOptimization(): Promise<void> {
    console.log('Performing full system optimization...');

    try {
      const optimizationPromises: Promise<any>[] = [];

      // Memory optimization
      if (this.config.enableMemoryOptimization) {
        optimizationPromises.push(memoryOptimizationService.forceCleanup());
      }

      // Image cache optimization
      if (this.config.enableImageCache) {
        optimizationPromises.push(imageCacheService.getCacheStats().then(stats => {
          if (stats.totalSize > 75 * 1024 * 1024) { // 75MB
            return imageCacheService.clearCache();
          }
        }));
      }

      // Background sync
      if (this.config.enableBackgroundSync) {
        optimizationPromises.push(backgroundSyncService.forcSync());
      }

      // Battery optimization
      if (this.config.enableBatteryOptimization) {
        const batteryStats = await batteryOptimizationService.getBatteryStats();
        if (batteryStats.batteryLevel < 30) {
          optimizationPromises.push(batteryOptimizationService.togglePowerSaveMode(true));
        }
      }

      await Promise.allSettled(optimizationPromises);
      
      console.log('Full system optimization completed');
      this.notifyStatusListeners();

    } catch (error) {
      console.error('Failed to perform full optimization:', error);
      throw error;
    }
  }

  async generateOptimizationReport(): Promise<{
    timestamp: Date;
    status: OptimizationStatus;
    recommendations: string[];
    metrics: any;
  }> {
    const status = await this.getOptimizationStatus();
    const recommendations: string[] = [];

    // Generate recommendations based on status
    if (status.overallHealth === 'poor' || status.overallHealth === 'fair') {
      recommendations.push('Consider performing a full optimization');
    }

    if (!status.imageCacheEnabled) {
      recommendations.push('Enable image caching for better performance');
    }

    if (!status.backgroundSyncEnabled) {
      recommendations.push('Enable background sync for seamless data updates');
    }

    // Get detailed metrics
    const metrics = this.config.enablePerformanceMonitoring ? 
      await performanceMonitoringService.generatePerformanceReport() : null;

    return {
      timestamp: new Date(),
      status,
      recommendations,
      metrics,
    };
  }

  async updateConfig(newConfig: Partial<OptimizationConfig>): Promise<void> {
    const oldConfig = { ...this.config };
    this.config = { ...this.config, ...newConfig };

    // Handle service enable/disable
    if (oldConfig.enableImageCache !== newConfig.enableImageCache) {
      if (newConfig.enableImageCache) {
        await imageCacheService.initialize();
      }
    }

    if (oldConfig.enableBackgroundSync !== newConfig.enableBackgroundSync) {
      if (newConfig.enableBackgroundSync) {
        await backgroundSyncService.startBackgroundSync();
      } else {
        backgroundSyncService.stopBackgroundSync();
      }
    }

    // Similar handling for other services...

    console.log('Optimization coordinator config updated:', this.config);
    this.notifyStatusListeners();
  }

  addStatusListener(listener: (status: OptimizationStatus) => void): () => void {
    this.statusListeners.push(listener);
    
    return () => {
      const index = this.statusListeners.indexOf(listener);
      if (index > -1) {
        this.statusListeners.splice(index, 1);
      }
    };
  }

  private async notifyStatusListeners(): Promise<void> {
    if (this.statusListeners.length === 0) return;

    try {
      const status = await this.getOptimizationStatus();
      this.statusListeners.forEach(listener => {
        try {
          listener(status);
        } catch (error) {
          console.error('Optimization status listener error:', error);
        }
      });
    } catch (error) {
      console.error('Failed to notify optimization status listeners:', error);
    }
  }

  async shutdown(): Promise<void> {
    console.log('Shutting down optimization services...');

    try {
      // Stop all services
      backgroundSyncService.stopBackgroundSync();
      memoryOptimizationService.stopMemoryOptimization();
      batteryOptimizationService.stopBatteryOptimization();
      performanceMonitoringService.stopPerformanceMonitoring();

      this.isInitialized = false;
      console.log('All optimization services shut down');

    } catch (error) {
      console.error('Failed to shutdown optimization services:', error);
    }
  }
}

export const optimizationCoordinator = new OptimizationCoordinator();