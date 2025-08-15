import { AppState, AppStateStatus } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { backgroundSyncService } from './backgroundSyncService';
import { memoryOptimizationService } from './memoryOptimizationService';

export interface BatteryConfig {
  lowBatteryThreshold: number; // percentage (0-100)
  enablePowerSaveMode: boolean;
  reducedSyncFrequency: number; // in milliseconds
  disableAnimations: boolean;
  reduceImageQuality: boolean;
  limitBackgroundTasks: boolean;
}

export interface BatteryStats {
  batteryLevel: number;
  isLowPowerMode: boolean;
  powerSaveModeActive: boolean;
  estimatedUsageTime: number; // in minutes
  lastOptimization: Date | null;
}

export interface PowerSaveSettings {
  syncInterval: number;
  imageQuality: number;
  animationsEnabled: boolean;
  backgroundTasksEnabled: boolean;
  cacheSize: number;
}

class BatteryOptimizationService {
  private readonly DEFAULT_CONFIG: BatteryConfig = {
    lowBatteryThreshold: 20, // 20%
    enablePowerSaveMode: true,
    reducedSyncFrequency: 15 * 60 * 1000, // 15 minutes
    disableAnimations: true,
    reduceImageQuality: true,
    limitBackgroundTasks: true,
  };

  private readonly BATTERY_CONFIG_KEY = 'battery_optimization_config';
  private readonly BATTERY_STATS_KEY = 'battery_optimization_stats';
  private readonly POWER_SAVE_SETTINGS_KEY = 'power_save_settings';

  private config: BatteryConfig;
  private appState: AppStateStatus = 'active';
  private batteryLevel = 100;
  private isLowPowerMode = false;
  private powerSaveModeActive = false;
  private originalSettings: PowerSaveSettings | null = null;
  private batteryMonitorTimer: NodeJS.Timeout | null = null;
  private listeners: ((stats: BatteryStats) => void)[] = [];

  constructor(config?: Partial<BatteryConfig>) {
    this.config = { ...this.DEFAULT_CONFIG, ...config };
    this.initializeAppStateListener();
  }

  private initializeAppStateListener(): void {
    AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      this.appState = nextAppState;

      if (nextAppState === 'background') {
        this.enableBackgroundOptimizations();
      } else if (nextAppState === 'active') {
        this.disableBackgroundOptimizations();
      }
    });
  }

  async startBatteryOptimization(): Promise<void> {
    console.log('Starting battery optimization service');
    
    // Load saved configuration
    await this.loadConfig();
    
    // Start battery monitoring
    this.startBatteryMonitoring();
    
    // Check initial battery state
    await this.checkBatteryState();
  }

  stopBatteryOptimization(): void {
    console.log('Stopping battery optimization service');
    this.stopBatteryMonitoring();
    
    // Restore original settings if power save mode was active
    if (this.powerSaveModeActive) {
      this.disablePowerSaveMode();
    }
  }

  private startBatteryMonitoring(): void {
    if (this.batteryMonitorTimer) return;

    // Monitor battery every 30 seconds
    this.batteryMonitorTimer = setInterval(async () => {
      await this.checkBatteryState();
    }, 30 * 1000);
  }

  private stopBatteryMonitoring(): void {
    if (this.batteryMonitorTimer) {
      clearInterval(this.batteryMonitorTimer);
      this.batteryMonitorTimer = null;
    }
  }

  private async checkBatteryState(): Promise<void> {
    try {
      // Note: React Native doesn't have built-in battery API
      // In a real implementation, you would use a native module or library
      // For now, we'll simulate battery monitoring
      
      const previousBatteryLevel = this.batteryLevel;
      const previousLowPowerMode = this.isLowPowerMode;
      
      // Simulate battery level (in real app, get from native module)
      // this.batteryLevel = await getBatteryLevel();
      // this.isLowPowerMode = await isLowPowerModeEnabled();
      
      // Check if we need to enable/disable power save mode
      if (this.config.enablePowerSaveMode) {
        const shouldEnablePowerSave = this.batteryLevel <= this.config.lowBatteryThreshold || this.isLowPowerMode;
        
        if (shouldEnablePowerSave && !this.powerSaveModeActive) {
          await this.enablePowerSaveMode();
        } else if (!shouldEnablePowerSave && this.powerSaveModeActive) {
          await this.disablePowerSaveMode();
        }
      }
      
      // Notify listeners if battery state changed
      if (this.batteryLevel !== previousBatteryLevel || this.isLowPowerMode !== previousLowPowerMode) {
        this.notifyListeners();
      }
      
    } catch (error) {
      console.error('Failed to check battery state:', error);
    }
  }

  private async enablePowerSaveMode(): Promise<void> {
    if (this.powerSaveModeActive) return;

    console.log('Enabling power save mode');
    
    try {
      // Save current settings
      this.originalSettings = await this.getCurrentSettings();
      
      // Apply power save settings
      const powerSaveSettings: PowerSaveSettings = {
        syncInterval: this.config.reducedSyncFrequency,
        imageQuality: this.config.reduceImageQuality ? 0.6 : 0.8,
        animationsEnabled: !this.config.disableAnimations,
        backgroundTasksEnabled: !this.config.limitBackgroundTasks,
        cacheSize: 50 * 1024 * 1024, // 50MB reduced cache
      };
      
      await this.applyPowerSaveSettings(powerSaveSettings);
      
      this.powerSaveModeActive = true;
      await this.savePowerSaveSettings(powerSaveSettings);
      
      console.log('Power save mode enabled');
      this.notifyListeners();
      
    } catch (error) {
      console.error('Failed to enable power save mode:', error);
    }
  }

  private async disablePowerSaveMode(): Promise<void> {
    if (!this.powerSaveModeActive || !this.originalSettings) return;

    console.log('Disabling power save mode');
    
    try {
      // Restore original settings
      await this.applyPowerSaveSettings(this.originalSettings);
      
      this.powerSaveModeActive = false;
      this.originalSettings = null;
      
      await AsyncStorage.removeItem(this.POWER_SAVE_SETTINGS_KEY);
      
      console.log('Power save mode disabled');
      this.notifyListeners();
      
    } catch (error) {
      console.error('Failed to disable power save mode:', error);
    }
  }

  private async getCurrentSettings(): Promise<PowerSaveSettings> {
    // Get current app settings
    return {
      syncInterval: 5 * 60 * 1000, // 5 minutes default
      imageQuality: 0.8,
      animationsEnabled: true,
      backgroundTasksEnabled: true,
      cacheSize: 100 * 1024 * 1024, // 100MB default
    };
  }

  private async applyPowerSaveSettings(settings: PowerSaveSettings): Promise<void> {
    try {
      // Apply sync frequency changes
      // Note: This would require integration with backgroundSyncService
      console.log(`Setting sync interval to ${settings.syncInterval}ms`);
      
      // Apply image quality changes
      // Note: This would require integration with imageCacheService
      console.log(`Setting image quality to ${settings.imageQuality}`);
      
      // Apply memory optimization changes
      memoryOptimizationService.updateConfig({
        maxMemoryUsage: settings.cacheSize,
        aggressiveCleanup: !settings.backgroundTasksEnabled,
      });
      
      // Apply animation settings
      // Note: This would require integration with UI components
      console.log(`Animations enabled: ${settings.animationsEnabled}`);
      
      // Apply background task limitations
      if (!settings.backgroundTasksEnabled) {
        // Reduce background processing
        console.log('Limiting background tasks');
      }
      
    } catch (error) {
      console.error('Failed to apply power save settings:', error);
      throw error;
    }
  }

  private async enableBackgroundOptimizations(): Promise<void> {
    console.log('Enabling background optimizations');
    
    try {
      // Reduce sync frequency in background
      // Stop non-essential background tasks
      // Reduce memory usage
      await memoryOptimizationService.performCleanup(true);
      
    } catch (error) {
      console.error('Failed to enable background optimizations:', error);
    }
  }

  private async disableBackgroundOptimizations(): Promise<void> {
    console.log('Disabling background optimizations');
    
    try {
      // Restore normal operation when app becomes active
      if (!this.powerSaveModeActive) {
        // Only restore if not in power save mode
        // Resume normal sync frequency
        // Resume background tasks
      }
      
    } catch (error) {
      console.error('Failed to disable background optimizations:', error);
    }
  }

  async getBatteryStats(): Promise<BatteryStats> {
    const lastOptimization = await this.getLastOptimizationTime();
    
    return {
      batteryLevel: this.batteryLevel,
      isLowPowerMode: this.isLowPowerMode,
      powerSaveModeActive: this.powerSaveModeActive,
      estimatedUsageTime: this.calculateEstimatedUsageTime(),
      lastOptimization,
    };
  }

  private calculateEstimatedUsageTime(): number {
    // Simple estimation based on battery level and usage patterns
    // In a real app, this would use historical data and current usage
    const baseUsageTime = 8 * 60; // 8 hours in minutes
    const batteryMultiplier = this.batteryLevel / 100;
    const powerSaveMultiplier = this.powerSaveModeActive ? 1.5 : 1.0;
    
    return Math.floor(baseUsageTime * batteryMultiplier * powerSaveMultiplier);
  }

  private async getLastOptimizationTime(): Promise<Date | null> {
    try {
      const statsJson = await AsyncStorage.getItem(this.BATTERY_STATS_KEY);
      if (statsJson) {
        const stats = JSON.parse(statsJson);
        return stats.lastOptimization ? new Date(stats.lastOptimization) : null;
      }
      return null;
    } catch (error) {
      console.error('Failed to get last optimization time:', error);
      return null;
    }
  }

  private async updateLastOptimizationTime(): Promise<void> {
    try {
      const stats = {
        lastOptimization: new Date().toISOString(),
      };
      await AsyncStorage.setItem(this.BATTERY_STATS_KEY, JSON.stringify(stats));
    } catch (error) {
      console.error('Failed to update last optimization time:', error);
    }
  }

  private async loadConfig(): Promise<void> {
    try {
      const configJson = await AsyncStorage.getItem(this.BATTERY_CONFIG_KEY);
      if (configJson) {
        const savedConfig = JSON.parse(configJson);
        this.config = { ...this.config, ...savedConfig };
      }
    } catch (error) {
      console.error('Failed to load battery config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      await AsyncStorage.setItem(this.BATTERY_CONFIG_KEY, JSON.stringify(this.config));
    } catch (error) {
      console.error('Failed to save battery config:', error);
    }
  }

  private async savePowerSaveSettings(settings: PowerSaveSettings): Promise<void> {
    try {
      await AsyncStorage.setItem(this.POWER_SAVE_SETTINGS_KEY, JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save power save settings:', error);
    }
  }

  async updateConfig(newConfig: Partial<BatteryConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();
    
    // Recheck battery state with new config
    await this.checkBatteryState();
    
    console.log('Battery optimization config updated:', this.config);
  }

  // Manual power save mode toggle
  async togglePowerSaveMode(enabled: boolean): Promise<void> {
    if (enabled && !this.powerSaveModeActive) {
      await this.enablePowerSaveMode();
    } else if (!enabled && this.powerSaveModeActive) {
      await this.disablePowerSaveMode();
    }
  }

  // Battery optimization recommendations
  async getOptimizationRecommendations(): Promise<string[]> {
    const recommendations: string[] = [];
    
    if (this.batteryLevel <= 30) {
      recommendations.push('Enable power save mode to extend battery life');
    }
    
    if (!this.powerSaveModeActive && this.batteryLevel <= this.config.lowBatteryThreshold) {
      recommendations.push('Consider reducing sync frequency');
      recommendations.push('Disable animations to save power');
    }
    
    const memoryStats = await memoryOptimizationService.getMemoryStats();
    if (memoryStats.totalMemoryUsage > 150 * 1024 * 1024) { // 150MB
      recommendations.push('Clear cache to reduce battery usage');
    }
    
    return recommendations;
  }

  addBatteryStatsListener(listener: (stats: BatteryStats) => void): () => void {
    this.listeners.push(listener);
    
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private async notifyListeners(): Promise<void> {
    if (this.listeners.length === 0) return;

    try {
      const stats = await this.getBatteryStats();
      this.listeners.forEach(listener => {
        try {
          listener(stats);
        } catch (error) {
          console.error('Battery stats listener error:', error);
        }
      });
    } catch (error) {
      console.error('Failed to notify battery stats listeners:', error);
    }
  }
}

export const batteryOptimizationService = new BatteryOptimizationService();