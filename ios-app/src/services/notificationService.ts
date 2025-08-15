import PushNotification from 'react-native-push-notification';
import PushNotificationIOS from '@react-native-community/push-notification-ios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface StudyReminder {
  id: string;
  title: string;
  message: string;
  scheduledTime: Date;
  repeatType: 'daily' | 'weekly' | 'custom';
  isActive: boolean;
}

class NotificationService {
  private initialized = false;

  async initialize() {
    if (this.initialized) return;

    // Configure push notifications
    PushNotification.configure({
      onRegister: (token) => {
        console.log('Push notification token:', token);
      },
      onNotification: (notification) => {
        console.log('Notification received:', notification);
        
        if (Platform.OS === 'ios') {
          notification.finish(PushNotificationIOS.FetchResult.NoData);
        }
      },
      onAction: (notification) => {
        console.log('Notification action:', notification.action);
      },
      onRegistrationError: (err) => {
        console.error('Push notification registration error:', err.message);
      },
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    // Create notification channel for Android
    if (Platform.OS === 'android') {
      PushNotification.createChannel(
        {
          channelId: 'study-reminders',
          channelName: 'Study Reminders',
          channelDescription: 'Notifications for study sessions',
          playSound: true,
          soundName: 'default',
          importance: 4,
          vibrate: true,
        },
        (created) => console.log(`Channel created: ${created}`)
      );
    }

    this.initialized = true;
  }

  async scheduleStudyReminder(reminder: StudyReminder): Promise<void> {
    await this.initialize();

    const notificationId = parseInt(reminder.id.replace(/\D/g, '').slice(-8)) || Math.floor(Math.random() * 1000000);

    PushNotification.localNotificationSchedule({
      id: notificationId,
      title: reminder.title,
      message: reminder.message,
      date: reminder.scheduledTime,
      repeatType: reminder.repeatType === 'daily' ? 'day' : reminder.repeatType === 'weekly' ? 'week' : undefined,
      channelId: 'study-reminders',
      playSound: true,
      soundName: 'default',
      actions: ['Study Now', 'Snooze'],
      userInfo: {
        reminderId: reminder.id,
        type: 'study-reminder',
      },
    });

    // Save reminder to storage
    await this.saveReminder(reminder);
  }

  async cancelStudyReminder(reminderId: string): Promise<void> {
    const notificationId = parseInt(reminderId.replace(/\D/g, '').slice(-8)) || 0;
    PushNotification.cancelLocalNotifications({ id: notificationId.toString() });
    
    // Remove from storage
    await this.removeReminder(reminderId);
  }

  async scheduleReviewReminder(cardCount: number, nextReviewTime: Date): Promise<void> {
    await this.initialize();

    const notificationId = Math.floor(Math.random() * 1000000);

    PushNotification.localNotificationSchedule({
      id: notificationId,
      title: 'Time to Review!',
      message: `You have ${cardCount} cards ready for review`,
      date: nextReviewTime,
      channelId: 'study-reminders',
      playSound: true,
      soundName: 'default',
      actions: ['Review Now', 'Later'],
      userInfo: {
        type: 'review-reminder',
        cardCount,
      },
    });
  }

  async scheduleDailyStudyReminder(hour: number, minute: number): Promise<void> {
    const now = new Date();
    const scheduledTime = new Date();
    scheduledTime.setHours(hour, minute, 0, 0);

    // If the time has passed today, schedule for tomorrow
    if (scheduledTime <= now) {
      scheduledTime.setDate(scheduledTime.getDate() + 1);
    }

    const reminder: StudyReminder = {
      id: 'daily-study-reminder',
      title: 'Daily Study Time',
      message: 'Time for your daily study session!',
      scheduledTime,
      repeatType: 'daily',
      isActive: true,
    };

    await this.scheduleStudyReminder(reminder);
  }

  async getScheduledReminders(): Promise<StudyReminder[]> {
    try {
      const remindersJson = await AsyncStorage.getItem('study-reminders');
      return remindersJson ? JSON.parse(remindersJson) : [];
    } catch (error) {
      console.error('Error loading reminders:', error);
      return [];
    }
  }

  private async saveReminder(reminder: StudyReminder): Promise<void> {
    try {
      const reminders = await this.getScheduledReminders();
      const updatedReminders = reminders.filter(r => r.id !== reminder.id);
      updatedReminders.push(reminder);
      await AsyncStorage.setItem('study-reminders', JSON.stringify(updatedReminders));
    } catch (error) {
      console.error('Error saving reminder:', error);
    }
  }

  private async removeReminder(reminderId: string): Promise<void> {
    try {
      const reminders = await this.getScheduledReminders();
      const updatedReminders = reminders.filter(r => r.id !== reminderId);
      await AsyncStorage.setItem('study-reminders', JSON.stringify(updatedReminders));
    } catch (error) {
      console.error('Error removing reminder:', error);
    }
  }

  async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'ios') {
      const permissions = await PushNotificationIOS.requestPermissions({
        alert: true,
        badge: true,
        sound: true,
      });
      return permissions.alert && permissions.badge && permissions.sound;
    }
    return true; // Android permissions are handled in manifest
  }

  async getBadgeCount(): Promise<number> {
    if (Platform.OS === 'ios') {
      return new Promise((resolve) => {
        PushNotificationIOS.getApplicationIconBadgeNumber(resolve);
      });
    }
    return 0;
  }

  async setBadgeCount(count: number): Promise<void> {
    if (Platform.OS === 'ios') {
      PushNotificationIOS.setApplicationIconBadgeNumber(count);
    } else {
      PushNotification.setApplicationIconBadgeNumber(count);
    }
  }
}

export const notificationService = new NotificationService();