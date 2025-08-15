import { Platform, AppState, AppStateStatus } from 'react-native';
import { notificationService } from './notificationService';
import { offlineStorage } from './offlineStorage';
import { widgetService } from './widgetService';
import { siriShortcutsService } from './siriShortcutsService';
import { hapticService } from './hapticService';

export interface iOSFeatureConfig {
  notifications: boolean;
  widgets: boolean;
  siriShortcuts: boolean;
  hapticFeedback: boolean;
  offlineMode: boolean;
}

class iOSIntegrationService {
  private appStateSubscription: any;
  private isInitialized = false;
  private config: iOSFeatureConfig = {
    notifications: true,
    widgets: true,
    siriShortcuts: true,
    hapticFeedback: true,
    offlineMode: true,
  };

  async initialize(config?: Partial<iOSFeatureConfig>): Promise<void> {
    if (this.isInitialized || Platform.OS !== 'ios') return;

    // Update configuration
    this.config = { ...this.config, ...config };

    try {
      // Initialize core services
      await this.initializeServices();
      
      // Set up app state monitoring
      this.setupAppStateHandling();
      
      // Set up periodic tasks
      this.setupPeriodicTasks();
      
      this.isInitialized = true;
      console.log('iOS integration services initialized successfully');
    } catch (error) {
      console.error('Error initializing iOS integration services:', error);
      throw error;
    }
  }

  private async initializeServices(): Promise<void> {
    const initPromises: Promise<void>[] = [];

    // Initialize notifications
    if (this.config.notifications) {
      initPromises.push(this.initializeNotifications());
    }

    // Initialize Siri shortcuts
    if (this.config.siriShortcuts) {
      initPromises.push(this.initializeSiriShortcuts());
    }

    // Initialize widgets
    if (this.config.widgets) {
      initPromises.push(this.initializeWidgets());
    }

    // Initialize haptic feedback
    if (this.config.hapticFeedback) {
      hapticService.setEnabled(true);
    }

    await Promise.all(initPromises);
  }

  private async initializeNotifications(): Promise<void> {
    try {
      await notificationService.initialize();
      const hasPermission = await notificationService.requestPermissions();
      
      if (hasPermission) {
        // Set up default daily study reminder
        await notificationService.scheduleDailyStudyReminder(19, 0); // 7 PM
        console.log('Notifications initialized successfully');
      } else {
        console.warn('Notification permissions not granted');
      }
    } catch (error) {
      console.error('Error initializing notifications:', error);
    }
  }

  private async initializeSiriShortcuts(): Promise<void> {
    try {
      await siriShortcutsService.initializeSiriShortcuts();
      console.log('Siri shortcuts initialized successfully');
    } catch (error) {
      console.error('Error initializing Siri shortcuts:', error);
    }
  }

  private async initializeWidgets(): Promise<void> {
    try {
      await widgetService.createStudyProgressWidget();
      await widgetService.scheduleWidgetUpdates();
      console.log('Widgets initialized successfully');
    } catch (error) {
      console.error('Error initializing widgets:', error);
    }
  }

  private setupAppStateHandling(): void {
    this.appStateSubscription = AppState.addEventListener(
      'change',
      this.handleAppStateChange.bind(this)
    );
  }

  private async handleAppStateChange(nextAppState: AppStateStatus): Promise<void> {
    try {
      if (nextAppState === 'active') {
        // App became active
        await this.onAppBecameActive();
      } else if (nextAppState === 'background') {
        // App went to background
        await this.onAppWentToBackground();
      }
    } catch (error) {
      console.error('Error handling app state change:', error);
    }
  }

  private async onAppBecameActive(): Promise<void> {
    // Update widgets when app becomes active
    if (this.config.widgets) {
      await widgetService.updateStudyProgressWidget();
    }

    // Update Siri shortcut predictions
    if (this.config.siriShortcuts) {
      await siriShortcutsService.updateShortcutPredictions();
    }

    // Clear badge count
    if (this.config.notifications) {
      await notificationService.setBadgeCount(0);
    }

    // Sync offline data if needed
    if (this.config.offlineMode) {
      await this.syncOfflineData();
    }
  }

  private async onAppWentToBackground(): Promise<void> {
    // Update badge count with due cards
    if (this.config.notifications) {
      try {
        const dueCards = await offlineStorage.getDueCards();
        await notificationService.setBadgeCount(dueCards.length);
      } catch (error) {
        console.error('Error updating badge count:', error);
      }
    }

    // Update widgets
    if (this.config.widgets) {
      await widgetService.updateStudyProgressWidget();
    }

    // Save current state
    await this.saveAppState();
  }

  private setupPeriodicTasks(): void {
    // Update widgets every 15 minutes when app is active
    if (this.config.widgets) {
      setInterval(async () => {
        if (AppState.currentState === 'active') {
          await widgetService.updateStudyProgressWidget();
        }
      }, 15 * 60 * 1000); // 15 minutes
    }

    // Update Siri shortcuts daily
    if (this.config.siriShortcuts) {
      setInterval(async () => {
        await siriShortcutsService.updateShortcutPredictions();
      }, 24 * 60 * 60 * 1000); // 24 hours
    }
  }

  private async syncOfflineData(): Promise<void> {
    try {
      // This would sync with the backend when online
      // For now, just update local data
      const pendingChanges = await offlineStorage.getPendingChanges();
      console.log(`Found ${pendingChanges.length} pending changes to sync`);
      
      // In a real implementation, you would sync these changes with the backend
      // and then clear them once successfully synced
    } catch (error) {
      console.error('Error syncing offline data:', error);
    }
  }

  private async saveAppState(): Promise<void> {
    try {
      const appState = {
        lastActiveTime: new Date().toISOString(),
        version: '1.0.0',
      };
      
      await offlineStorage.saveUserPreferences({
        ...await offlineStorage.getUserPreferences(),
        appState,
      });
    } catch (error) {
      console.error('Error saving app state:', error);
    }
  }

  // Public methods for handling specific iOS features

  async handleSiriShortcut(identifier: string, parameters?: Record<string, any>): Promise<any> {
    if (!this.config.siriShortcuts) {
      return { success: false, message: 'Siri shortcuts are disabled' };
    }

    return await siriShortcutsService.handleSiriShortcut(identifier, parameters);
  }

  async handleWidgetTap(action: string): Promise<void> {
    if (!this.config.widgets) return;

    hapticService.buttonPress();
    await widgetService.handleWidgetTap(action);
  }

  async scheduleStudyReminder(time: { hour: number; minute: number }): Promise<void> {
    if (!this.config.notifications) return;

    await notificationService.scheduleDailyStudyReminder(time.hour, time.minute);
  }

  async updateStudyProgress(): Promise<void> {
    const tasks: Promise<void>[] = [];

    if (this.config.widgets) {
      tasks.push(widgetService.updateStudyProgressWidget());
    }

    if (this.config.notifications) {
      tasks.push(this.updateNotificationBadge());
    }

    await Promise.all(tasks);
  }

  private async updateNotificationBadge(): Promise<void> {
    try {
      const dueCards = await offlineStorage.getDueCards();
      await notificationService.setBadgeCount(dueCards.length);
    } catch (error) {
      console.error('Error updating notification badge:', error);
    }
  }

  async getStudyStats(): Promise<any> {
    return await widgetService.getStudyStats();
  }

  async exportOfflineData(): Promise<any> {
    if (!this.config.offlineMode) {
      throw new Error('Offline mode is disabled');
    }

    return await offlineStorage.exportOfflineData();
  }

  async importOfflineData(data: any): Promise<void> {
    if (!this.config.offlineMode) {
      throw new Error('Offline mode is disabled');
    }

    await offlineStorage.importOfflineData(data);
    await this.updateStudyProgress();
  }

  async enableFeature(feature: keyof iOSFeatureConfig): Promise<void> {
    this.config[feature] = true;
    
    switch (feature) {
      case 'notifications':
        await this.initializeNotifications();
        break;
      case 'widgets':
        await this.initializeWidgets();
        break;
      case 'siriShortcuts':
        await this.initializeSiriShortcuts();
        break;
      case 'hapticFeedback':
        hapticService.setEnabled(true);
        break;
    }
  }

  async disableFeature(feature: keyof iOSFeatureConfig): Promise<void> {
    this.config[feature] = false;
    
    switch (feature) {
      case 'widgets':
        await widgetService.removeStudyProgressWidget();
        break;
      case 'siriShortcuts':
        await siriShortcutsService.removeAllShortcuts();
        break;
      case 'hapticFeedback':
        hapticService.setEnabled(false);
        break;
    }
  }

  getFeatureConfig(): iOSFeatureConfig {
    return { ...this.config };
  }

  async cleanup(): Promise<void> {
    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
    }

    this.isInitialized = false;
  }

  // Achievement system integration
  async checkForAchievements(): Promise<void> {
    try {
      const stats = await this.getStudyStats();
      
      // Check for study streak achievements
      if (stats.studyStreak > 0 && stats.studyStreak % 7 === 0) {
        hapticService.streakAchievement();
        
        if (this.config.notifications) {
          await notificationService.scheduleStudyReminder({
            id: `streak_${stats.studyStreak}`,
            title: 'Study Streak Achievement!',
            message: `Congratulations! You've maintained a ${stats.studyStreak}-day study streak!`,
            scheduledTime: new Date(),
            repeatType: 'custom',
            isActive: true,
          });
        }
      }

      // Check for review milestones
      if (stats.reviewedToday > 0 && stats.reviewedToday % 50 === 0) {
        hapticService.sessionComplete();
      }
    } catch (error) {
      console.error('Error checking for achievements:', error);
    }
  }
}

export const iOSIntegrationService = new iOSIntegrationService();