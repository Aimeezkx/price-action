/**
 * Error Notifications Hook
 * React hook for managing error notifications with retry functionality
 * Integrates with the error notification manager
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  ErrorNotificationState, 
  NotificationEvent, 
  NotificationOptions,
  errorNotificationManager,
  ErrorContext
} from '../lib/error-notification-manager';
import { ClassifiedError, NetworkErrorType } from '../lib/error-handling';

export interface UseErrorNotificationsReturn {
  notifications: ErrorNotificationState[];
  addNotification: (error: ClassifiedError, options?: NotificationOptions) => string;
  addNotificationFromError: (error: Error, statusCode?: number, context?: ErrorContext, options?: NotificationOptions) => string;
  dismissNotification: (id: string) => void;
  retryNotification: (id: string) => void;
  clearAll: () => void;
  clearByType: (errorType: NetworkErrorType) => void;
  stats: {
    total: number;
    active: number;
    byType: Record<NetworkErrorType, number>;
    byPriority: Record<string, number>;
  };
}

export const useErrorNotifications = (): UseErrorNotificationsReturn => {
  const [notifications, setNotifications] = useState<ErrorNotificationState[]>([]);
  const [stats, setStats] = useState(errorNotificationManager.getNotificationStats());

  // Update notifications when manager state changes
  const updateNotifications = useCallback(() => {
    setNotifications(errorNotificationManager.getActiveNotifications());
    setStats(errorNotificationManager.getNotificationStats());
  }, []);

  useEffect(() => {
    // Initial load
    updateNotifications();

    // Listen for notification events
    const unsubscribe = errorNotificationManager.addEventListener((event: NotificationEvent) => {
      updateNotifications();
    });

    return unsubscribe;
  }, [updateNotifications]);

  const addNotification = useCallback((error: ClassifiedError, options?: NotificationOptions): string => {
    return errorNotificationManager.addNotification(error, options);
  }, []);

  const addNotificationFromError = useCallback((
    error: Error, 
    statusCode?: number, 
    context?: ErrorContext, 
    options?: NotificationOptions
  ): string => {
    return errorNotificationManager.createNotificationFromError(error, statusCode, context, options);
  }, []);

  const dismissNotification = useCallback((id: string) => {
    errorNotificationManager.dismissNotification(id);
  }, []);

  const retryNotification = useCallback((id: string) => {
    errorNotificationManager.retryNotification(id);
  }, []);

  const clearAll = useCallback(() => {
    errorNotificationManager.clearAllNotifications();
  }, []);

  const clearByType = useCallback((errorType: NetworkErrorType) => {
    errorNotificationManager.clearNotificationsByType(errorType);
  }, []);

  return {
    notifications,
    addNotification,
    addNotificationFromError,
    dismissNotification,
    retryNotification,
    clearAll,
    clearByType,
    stats
  };
};

// Specialized hooks for common use cases

export const useApiErrorHandler = () => {
  const { addNotificationFromError } = useErrorNotifications();

  const handleApiError = useCallback((
    error: Error,
    operation: string,
    onRetry?: () => void
  ) => {
    const statusCode = (error as any).status || (error as any).statusCode;
    
    return addNotificationFromError(error, statusCode, {
      operation,
      userAction: 'api_request'
    }, {
      onRetry,
      showRetryButton: true,
      showTechnicalDetails: process.env.NODE_ENV === 'development'
    });
  }, [addNotificationFromError]);

  return { handleApiError };
};

export const useUploadErrorHandler = () => {
  const { addNotificationFromError } = useErrorNotifications();

  const handleUploadError = useCallback((
    error: Error,
    fileName?: string,
    onRetry?: () => void
  ) => {
    const statusCode = (error as any).status || (error as any).statusCode;
    
    return addNotificationFromError(error, statusCode, {
      operation: 'file_upload',
      resource: fileName,
      userAction: 'upload_file'
    }, {
      onRetry,
      showRetryButton: true,
      persistent: true, // Keep upload errors visible
      autoHide: false
    });
  }, [addNotificationFromError]);

  return { handleUploadError };
};

export const useConnectionErrorHandler = () => {
  const { addNotificationFromError, clearByType } = useErrorNotifications();

  const handleConnectionError = useCallback((
    error: Error,
    onRetry?: () => void
  ) => {
    // Clear previous connection errors to avoid spam
    clearByType(NetworkErrorType.CONNECTION_TIMEOUT);
    clearByType(NetworkErrorType.NETWORK_UNREACHABLE);
    
    const statusCode = (error as any).status || (error as any).statusCode;
    
    return addNotificationFromError(error, statusCode, {
      operation: 'connection',
      userAction: 'connect_to_server'
    }, {
      onRetry,
      showRetryButton: true,
      priority: 'high',
      autoHideDelay: 10000 // Longer delay for connection issues
    });
  }, [addNotificationFromError, clearByType]);

  return { handleConnectionError };
};