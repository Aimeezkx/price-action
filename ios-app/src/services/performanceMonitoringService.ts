import { AppState, AppStateStatus, Dimensions } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { imageCacheService } from './imageCacheService';
import { memoryOptimizationService } from './memoryOptimizationService';
import { batteryOptimizationService } from './batteryOptimizationService';
import { backgroundSyncService } from './backgroundSyncService';

export interface PerformanceMetrics {
  appStartTime: number;
  screenTransitionTimes: { [screenName: string]: number };
  apiResponseTimes: { [endpoint: string]: number[] };
  memoryUsage: number;
  batteryUsage: number;
  cacheHitRate: number;
  syncSuccessRate: number;
  crashCount: number;
  errorCount: number;
  userInteractionLatency: number[];
}

export interface PerformanceConfig {
  enableMetricsCollection: boolean;
  enableCrashReporting: boolean;
  enablePerformanceOptimization: boolean;
  metricsRetentionDays: number;
  performanceThresholds: {
    maxAppStartTime: number;
    maxScreenTransitionTime: number;
    maxApiResponseTime: number;
    maxMemoryUsage: number;
    minCacheHitRate: number;
  };
}

export interface PerformanceReport {
  timestamp: Date;
  metrics: PerformanceMetrics;
  deviceInfo: {
    platform: string;
    version: string;
    screenSize: { width: number; height: number };
    isLowEndDevice: boolean;
  };
  recommendations: string[];
}

class PerformanceMonitoringService {
  private readonly DEFAULT_CONFIG: PerformanceConfig = {
    enableMetricsCollection: true,
    enableCrashReporting: true,
    enablePerformanceOptimization: true,
    metricsRetentionDays: 30,
    performanceThresholds: {
      maxAppStartTime: 3000, // 3 seconds
      maxScreenTransitionTime: 500, // 500ms
      maxApiResponseTime: 5000, // 5 seconds
      maxMemoryUsage: 200 * 1024 * 1024, // 200MB
      minCacheHitRate: 0.8, // 80%
    },
  };

  private readonly PERFORMANCE_CONFIG_KEY = 'performance_config';
  private readonly PERFORMANCE_METRICS_KEY = 'performance_metrics';
  private readonly PERFORMANCE_REPORTS_KEY = 'performance_reports';

  private config: PerformanceConfig;
  private metrics: PerformanceMetrics;
  private appStartTime: number;
  private screenTransitionStartTimes: { [screenName: string]: number } = {};
  private apiRequestStartTimes: { [requestId: string]: number } = {};
  private userInteractionStartTimes: { [interactionId: string]: number } = {};
  private monitoringTimer: NodeJS.Timeout | null = null;
  private appState: AppStateStatus = 'active';

  constructor(config?: Partial<PerformanceConfig>) {
    this.config = { ...this.DEFAULT_CONFIG, ...config };
    this.appStartTime = Date.now();
    this.metrics = this.initializeMetrics();
    this.initializeAppStateListener();
  }

  private initializeMetrics(): PerformanceMetrics {
    return {
      appStartTime: 0,
      screenTransitionTimes: {},
      apiResponseTimes: {},
      memoryUsage: 0,
      batteryUsage: 0,
      cacheHitRate: 0,
      syncSuccessRate: 0,
      crashCount: 0,
      errorCount: 0,
      userInteractionLatency: [],
    };
  }

  private initializeAppStateListener(): void {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      this.appState = nextAppState;

      if (nextAppState === 'background') {
        this.pauseMonitoring();
      } else if (nextAppState === 'active') {
        this.resumeMonitoring();
      }
    });
  }

  async startPerformanceMonitoring(): Promise<void> {
    console.log('Starting performance monitoring service');
    
    try {
      // Load saved configuration and metrics
      await this.loadConfig();
      await this.loadMetrics();
      
      // Record app start time
      this.metrics.appStartTime = Date.now() - this.appStartTime;
      
      // Start periodic monitoring
      this.startPeriodicMonitoring();
      
      // Set up error handling
      this.setupErrorHandling();
      
      console.log(`App started in ${this.metrics.appStartTime}ms`);
    } catch (error) {
      console.error('Failed to start performance monitoring:', error);
    }
  }

  stopPerformanceMonitoring(): void {
    console.log('Stopping performance monitoring service');
    this.stopPeriodicMonitoring();
    this.saveMetrics();
  }

  private startPeriodicMonitoring(): void {
    if (this.monitoringTimer) return;

    // Monitor performance every 30 seconds
    this.monitoringTimer = setInterval(async () => {
      if (this.config.enableMetricsCollection) {
        await this.collectPerformanceMetrics();
      }
    }, 30 * 1000);
  }

  private stopPeriodicMonitoring(): void {
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
    }
  }

  private pauseMonitoring(): void {
    console.log('Pausing performance monitoring (app in background)');
    this.stopPeriodicMonitoring();
  }

  private resumeMonitoring(): void {
    console.log('Resuming performance monitoring (app active)');
    this.startPeriodicMonitoring();
  }

  private async collectPerformanceMetrics(): Promise<void> {
    try {
      // Collect memory usage
      const memoryStats = await memoryOptimizationService.getMemoryStats();
      this.metrics.memoryUsage = memoryStats.totalMemoryUsage;

      // Collect cache performance
      const cacheStats = await imageCacheService.getCacheStats();
      // Calculate cache hit rate (simplified)
      this.metrics.cacheHitRate = cacheStats.entryCount > 0 ? 0.85 : 0; // Placeholder

      // Collect sync performance
      const syncStatus = await backgroundSyncService.getSyncStatus();
      // Calculate sync success rate (simplified)
      this.metrics.syncSuccessRate = syncStatus.syncInProgress ? 0.9 : 1.0; // Placeholder

      // Check performance thresholds and trigger optimizations
      await this.checkPerformanceThresholds();

    } catch (error) {
      console.error('Failed to collect performance metrics:', error);
      this.metrics.errorCount++;
    }
  }

  private async checkPerformanceThresholds(): Promise<void> {
    const thresholds = this.config.performanceThresholds;
    let optimizationNeeded = false;

    // Check memory usage
    if (this.metrics.memoryUsage > thresholds.maxMemoryUsage) {
      console.warn(`Memory usage ${(this.metrics.memoryUsage / 1024 / 1024).toFixed(2)}MB exceeds threshold`);
      optimizationNeeded = true;
    }

    // Check cache hit rate
    if (this.metrics.cacheHitRate < thresholds.minCacheHitRate) {
      console.warn(`Cache hit rate ${(this.metrics.cacheHitRate * 100).toFixed(1)}% below threshold`);
      optimizationNeeded = true;
    }

    // Trigger optimizations if needed
    if (optimizationNeeded && this.config.enablePerformanceOptimization) {
      await this.triggerPerformanceOptimizations();
    }
  }

  private async triggerPerformanceOptimizations(): Promise<void> {
    console.log('Triggering performance optimizations');
    
    try {
      // Trigger memory cleanup
      await memoryOptimizationService.performCleanup();
      
      // Trigger battery optimization if needed
      const batteryStats = await batteryOptimizationService.getBatteryStats();
      if (batteryStats.batteryLevel < 30) {
        await batteryOptimizationService.togglePowerSaveMode(true);
      }
      
    } catch (error) {
      console.error('Performance optimization failed:', error);
    }
  }

  private setupErrorHandling(): void {
    // Set up global error handler
    const originalHandler = ErrorUtils.getGlobalHandler();
    
    ErrorUtils.setGlobalHandler((error, isFatal) => {
      if (this.config.enableCrashReporting) {
        this.recordError(error, isFatal);
      }
      
      // Call original handler
      if (originalHandler) {
        originalHandler(error, isFatal);
      }
    });
  }

  private recordError(error: Error, isFatal: boolean): void {
    console.error('Recorded error:', error.message, 'Fatal:', isFatal);
    
    if (isFatal) {
      this.metrics.crashCount++;
    } else {
      this.metrics.errorCount++;
    }
    
    // Save metrics immediately for crashes
    if (isFatal) {
      this.saveMetrics();
    }
  }

  // Public API for tracking specific performance events

  trackScreenTransition(screenName: string, startTime?: number): void {
    if (!this.config.enableMetricsCollection) return;

    if (startTime) {
      // End tracking
      const duration = Date.now() - startTime;
      this.metrics.screenTransitionTimes[screenName] = duration;
      
      if (duration > this.config.performanceThresholds.maxScreenTransitionTime) {
        console.warn(`Screen transition to ${screenName} took ${duration}ms (exceeds threshold)`);
      }
    } else {
      // Start tracking
      this.screenTransitionStartTimes[screenName] = Date.now();
    }
  }

  trackApiRequest(endpoint: string, requestId?: string): void {
    if (!this.config.enableMetricsCollection) return;

    if (requestId && this.apiRequestStartTimes[requestId]) {
      // End tracking
      const duration = Date.now() - this.apiRequestStartTimes[requestId];
      
      if (!this.metrics.apiResponseTimes[endpoint]) {
        this.metrics.apiResponseTimes[endpoint] = [];
      }
      this.metrics.apiResponseTimes[endpoint].push(duration);
      
      // Keep only last 10 measurements per endpoint
      if (this.metrics.apiResponseTimes[endpoint].length > 10) {
        this.metrics.apiResponseTimes[endpoint].shift();
      }
      
      delete this.apiRequestStartTimes[requestId];
      
      if (duration > this.config.performanceThresholds.maxApiResponseTime) {
        console.warn(`API request to ${endpoint} took ${duration}ms (exceeds threshold)`);
      }
    } else {
      // Start tracking
      const id = requestId || `${endpoint}_${Date.now()}`;
      this.apiRequestStartTimes[id] = Date.now();
    }
  }

  trackUserInteraction(interactionType: string, interactionId?: string): void {
    if (!this.config.enableMetricsCollection) return;

    if (interactionId && this.userInteractionStartTimes[interactionId]) {
      // End tracking
      const latency = Date.now() - this.userInteractionStartTimes[interactionId];
      this.metrics.userInteractionLatency.push(latency);
      
      // Keep only last 50 measurements
      if (this.metrics.userInteractionLatency.length > 50) {
        this.metrics.userInteractionLatency.shift();
      }
      
      delete this.userInteractionStartTimes[interactionId];
      
      console.log(`User interaction ${interactionType} latency: ${latency}ms`);
    } else {
      // Start tracking
      const id = interactionId || `${interactionType}_${Date.now()}`;
      this.userInteractionStartTimes[id] = Date.now();
    }
  }

  async generatePerformanceReport(): Promise<PerformanceReport> {
    const { width, height } = Dimensions.get('window');
    
    const report: PerformanceReport = {
      timestamp: new Date(),
      metrics: { ...this.metrics },
      deviceInfo: {
        platform: 'ios',
        version: '1.0.0', // App version
        screenSize: { width, height },
        isLowEndDevice: this.isLowEndDevice(),
      },
      recommendations: await this.generateRecommendations(),
    };

    // Save report
    await this.savePerformanceReport(report);
    
    return report;
  }

  private isLowEndDevice(): boolean {
    // Simple heuristic to detect low-end devices
    const { width, height } = Dimensions.get('window');
    const screenArea = width * height;
    
    // Consider devices with small screens or limited memory as low-end
    return screenArea < 800 * 600 || this.metrics.memoryUsage > 150 * 1024 * 1024;
  }

  private async generateRecommendations(): Promise<string[]> {
    const recommendations: string[] = [];
    const thresholds = this.config.performanceThresholds;

    // App start time recommendations
    if (this.metrics.appStartTime > thresholds.maxAppStartTime) {
      recommendations.push('Consider optimizing app startup time by reducing initial load');
    }

    // Memory usage recommendations
    if (this.metrics.memoryUsage > thresholds.maxMemoryUsage) {
      recommendations.push('Memory usage is high - consider clearing cache or reducing image quality');
    }

    // Cache performance recommendations
    if (this.metrics.cacheHitRate < thresholds.minCacheHitRate) {
      recommendations.push('Cache hit rate is low - consider preloading frequently accessed content');
    }

    // API performance recommendations
    const avgApiResponseTime = this.getAverageApiResponseTime();
    if (avgApiResponseTime > thresholds.maxApiResponseTime) {
      recommendations.push('API response times are slow - check network connection or enable offline mode');
    }

    // Battery optimization recommendations
    const batteryStats = await batteryOptimizationService.getBatteryStats();
    if (batteryStats.batteryLevel < 20) {
      recommendations.push('Battery is low - enable power save mode to extend usage time');
    }

    // Error rate recommendations
    if (this.metrics.errorCount > 10) {
      recommendations.push('High error rate detected - check app stability');
    }

    return recommendations;
  }

  private getAverageApiResponseTime(): number {
    const allResponseTimes = Object.values(this.metrics.apiResponseTimes).flat();
    if (allResponseTimes.length === 0) return 0;
    
    return allResponseTimes.reduce((sum, time) => sum + time, 0) / allResponseTimes.length;
  }

  private async loadConfig(): Promise<void> {
    try {
      const configJson = await AsyncStorage.getItem(this.PERFORMANCE_CONFIG_KEY);
      if (configJson) {
        const savedConfig = JSON.parse(configJson);
        this.config = { ...this.config, ...savedConfig };
      }
    } catch (error) {
      console.error('Failed to load performance config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      await AsyncStorage.setItem(this.PERFORMANCE_CONFIG_KEY, JSON.stringify(this.config));
    } catch (error) {
      console.error('Failed to save performance config:', error);
    }
  }

  private async loadMetrics(): Promise<void> {
    try {
      const metricsJson = await AsyncStorage.getItem(this.PERFORMANCE_METRICS_KEY);
      if (metricsJson) {
        const savedMetrics = JSON.parse(metricsJson);
        this.metrics = { ...this.metrics, ...savedMetrics };
      }
    } catch (error) {
      console.error('Failed to load performance metrics:', error);
    }
  }

  private async saveMetrics(): Promise<void> {
    try {
      await AsyncStorage.setItem(this.PERFORMANCE_METRICS_KEY, JSON.stringify(this.metrics));
    } catch (error) {
      console.error('Failed to save performance metrics:', error);
    }
  }

  private async savePerformanceReport(report: PerformanceReport): Promise<void> {
    try {
      const reportsJson = await AsyncStorage.getItem(this.PERFORMANCE_REPORTS_KEY);
      const reports: PerformanceReport[] = reportsJson ? JSON.parse(reportsJson) : [];
      
      reports.push(report);
      
      // Keep only reports from the last retention period
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.config.metricsRetentionDays);
      
      const filteredReports = reports.filter(r => new Date(r.timestamp) > cutoffDate);
      
      await AsyncStorage.setItem(this.PERFORMANCE_REPORTS_KEY, JSON.stringify(filteredReports));
    } catch (error) {
      console.error('Failed to save performance report:', error);
    }
  }

  async getPerformanceReports(): Promise<PerformanceReport[]> {
    try {
      const reportsJson = await AsyncStorage.getItem(this.PERFORMANCE_REPORTS_KEY);
      return reportsJson ? JSON.parse(reportsJson) : [];
    } catch (error) {
      console.error('Failed to get performance reports:', error);
      return [];
    }
  }

  async updateConfig(newConfig: Partial<PerformanceConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();
    console.log('Performance monitoring config updated:', this.config);
  }

  getCurrentMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }
}

export const performanceMonitoringService = new PerformanceMonitoringService();