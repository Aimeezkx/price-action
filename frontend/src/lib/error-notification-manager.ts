/**
 * Error Notification Manager
 * Manages error notifications, queuing, and user interaction
 * Provides centralized error notification handling with retry logic
 */

import { ClassifiedError, NetworkErrorType } from './error-handling';
import { ErrorContext, getContextualErrorMessage, getQuickActions, getSupportInfo } from './error-messages';

export interface NotificationOptions {
  autoHide?: boolean;
  autoHideDelay?: number;
  showRetryButton?: boolean;
  showTechnicalDetails?: boolean;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  persistent?: boolean;
  onRetry?: () => void;
  onDismiss?: () => void;
  context?: ErrorContext;
}

export interface ErrorNotificationState {
  id: string;
  error: ClassifiedError;
  options: NotificationOptions;
  timestamp: Date;
  dismissed: boolean;
  retryCount: number;
}

export type NotificationEventType =
  | 'notification_added'
  | 'notification_dismissed'
  | 'notification_retry'
  | 'notification_expired'
  | 'queue_cleared';

export interface NotificationEvent {
  type: NotificationEventType;
  notification?: ErrorNotificationState;
  timestamp: Date;
}

export class ErrorNotificationManager {
  private notifications: Map<string, ErrorNotificationState> = new Map();
  private listeners: Array<(event: NotificationEvent) => void> = [];
  private maxNotifications = 5;
  private defaultAutoHideDelay = 8000;

  public addNotification(
    error: ClassifiedError,
    options: NotificationOptions = {}
  ): string {
    const id = this.generateNotificationId();

    // Apply default options
    const finalOptions: NotificationOptions = {
      autoHide: true,
      autoHideDelay: this.defaultAutoHideDelay,
      showRetryButton: error.isRetryable,
      showTechnicalDetails: false,
      priority: this.determinePriority(error),
      persistent: false,
      ...options
    };

    // Create notification state
    const notification: ErrorNotificationState = {
      id,
      error,
      options: finalOptions,
      timestamp: new Date(),
      dismissed: false,
      retryCount: 0
    };

    // Handle queue overflow
    this.enforceMaxNotifications();

    // Add to queue
    this.notifications.set(id, notification);

    // Set up auto-hide if enabled
    if (finalOptions.autoHide && finalOptions.autoHideDelay && !finalOptions.persistent) {
      setTimeout(() => {
        this.expireNotification(id);
      }, finalOptions.autoHideDelay);
    }

    // Emit event
    this.emitEvent({
      type: 'notification_added',
      notification,
      timestamp: new Date()
    });

    return id;
  }

  public dismissNotification(id: string): boolean {
    const notification = this.notifications.get(id);
    if (!notification || notification.dismissed) {
      return false;
    }

    notification.dismissed = true;
    notification.options.onDismiss?.();

    this.emitEvent({
      type: 'notification_dismissed',
      notification,
      timestamp: new Date()
    });

    // Remove from queue after a short delay to allow for animations
    setTimeout(() => {
      this.notifications.delete(id);
    }, 300);

    return true;
  }

  public retryNotification(id: string): boolean {
    const notification = this.notifications.get(id);
    if (!notification || notification.dismissed) {
      return false;
    }

    notification.retryCount++;

    // Update context with retry count
    if (notification.options.context) {
      notification.options.context.retryCount = notification.retryCount;
    }

    notification.options.onRetry?.();

    this.emitEvent({
      type: 'notification_retry',
      notification,
      timestamp: new Date()
    });

    // Auto-dismiss after retry
    this.dismissNotification(id);

    return true;
  }

  public getActiveNotifications(): ErrorNotificationState[] {
    return Array.from(this.notifications.values())
      .filter(n => !n.dismissed)
      .sort((a, b) => {
        // Sort by priority first, then by timestamp
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        const aPriority = priorityOrder[a.options.priority || 'medium'];
        const bPriority = priorityOrder[b.options.priority || 'medium'];

        if (aPriority !== bPriority) {
          return bPriority - aPriority;
        }

        return b.timestamp.getTime() - a.timestamp.getTime();
      });
  }

  public getNotification(id: string): ErrorNotificationState | undefined {
    return this.notifications.get(id);
  }

  public clearAllNotifications(): void {
    const activeNotifications = this.getActiveNotifications();

    activeNotifications.forEach(notification => {
      notification.dismissed = true;
      notification.options.onDismiss?.();
    });

    this.notifications.clear();

    this.emitEvent({
      type: 'queue_cleared',
      timestamp: new Date()
    });
  }

  public clearNotificationsByType(errorType: NetworkErrorType): void {
    const toRemove: string[] = [];

    this.notifications.forEach((notification, id) => {
      if (notification.error.type === errorType && !notification.dismissed) {
        notification.dismissed = true;
        notification.options.onDismiss?.();
        toRemove.push(id);
      }
    });

    toRemove.forEach(id => {
      setTimeout(() => {
        this.notifications.delete(id);
      }, 300);
    });
  }

  public addEventListener(listener: (event: NotificationEvent) => void): () => void {
    this.listeners.push(listener);

    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  public getNotificationStats(): {
    total: number;
    active: number;
    byType: Record<NetworkErrorType, number>;
    byPriority: Record<string, number>;
  } {
    const active = this.getActiveNotifications();
    const byType: Record<NetworkErrorType, number> = {} as Record<NetworkErrorType, number>;
    const byPriority: Record<string, number> = {};

    active.forEach(notification => {
      const type = notification.error.type;
      const priority = notification.options.priority || 'medium';

      byType[type] = (byType[type] || 0) + 1;
      byPriority[priority] = (byPriority[priority] || 0) + 1;
    });

    return {
      total: this.notifications.size,
      active: active.length,
      byType,
      byPriority
    };
  }

  public createNotificationFromError(
    error: Error,
    statusCode?: number,
    context?: ErrorContext,
    options?: NotificationOptions
  ): string {
    // Import the classifier here to avoid circular dependencies
    const { classifyError } = require('./error-handling');
    const classifiedError = classifyError(error, statusCode);

    return this.addNotification(classifiedError, {
      ...options,
      context
    });
  }

  private generateNotificationId(): string {
    return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private determinePriority(error: ClassifiedError): 'low' | 'medium' | 'high' | 'critical' {
    switch (error.type) {
      case NetworkErrorType.CORS_ERROR:
      case NetworkErrorType.SERVICE_UNAVAILABLE:
        return 'critical';

      case NetworkErrorType.SERVER_ERROR:
      case NetworkErrorType.NETWORK_UNREACHABLE:
      case NetworkErrorType.DNS_RESOLUTION_FAILED:
        return 'high';

      case NetworkErrorType.CONNECTION_TIMEOUT:
      case NetworkErrorType.CLIENT_ERROR:
        return 'medium';

      case NetworkErrorType.RATE_LIMITED:
        return 'low';

      default:
        return 'medium';
    }
  }

  private enforceMaxNotifications(): void {
    const active = this.getActiveNotifications();

    if (active.length >= this.maxNotifications) {
      // Remove oldest low-priority notifications first
      const toRemove = active
        .filter(n => n.options.priority === 'low' && !n.options.persistent)
        .slice(0, active.length - this.maxNotifications + 1);

      toRemove.forEach(notification => {
        this.dismissNotification(notification.id);
      });
    }
  }

  private expireNotification(id: string): void {
    const notification = this.notifications.get(id);
    if (notification && !notification.dismissed && !notification.options.persistent) {
      notification.dismissed = true;

      this.emitEvent({
        type: 'notification_expired',
        notification,
        timestamp: new Date()
      });

      setTimeout(() => {
        this.notifications.delete(id);
      }, 300);
    }
  }

  private emitEvent(event: NotificationEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in notification event listener:', error);
      }
    });
  }

  // Configuration methods
  public setMaxNotifications(max: number): void {
    this.maxNotifications = Math.max(1, max);
  }

  public setDefaultAutoHideDelay(delay: number): void {
    this.defaultAutoHideDelay = Math.max(1000, delay);
  }
}

// Export singleton instance
export const errorNotificationManager = new ErrorNotificationManager();

// Convenience functions
export const showErrorNotification = (
  error: ClassifiedError,
  options?: NotificationOptions
) => errorNotificationManager.addNotification(error, options);

export const showErrorFromException = (
  error: Error,
  statusCode?: number,
  context?: ErrorContext,
  options?: NotificationOptions
) => errorNotificationManager.createNotificationFromError(error, statusCode, context, options);

export const dismissErrorNotification = (id: string) =>
  errorNotificationManager.dismissNotification(id);

export const retryErrorNotification = (id: string) =>
  errorNotificationManager.retryNotification(id);

export const clearAllErrorNotifications = () =>
  errorNotificationManager.clearAllNotifications();
