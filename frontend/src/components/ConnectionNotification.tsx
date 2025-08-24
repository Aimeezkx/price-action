/**
 * Connection notification component
 * Shows toast-style notifications for connection status changes
 */

import { useState, useEffect } from 'react';
import { healthMonitor, type HealthStatus } from '../lib/health-monitor';

interface ConnectionNotificationProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  autoHide?: boolean;
  hideDelay?: number;
}

export function ConnectionNotification({ 
  position = 'top-right',
  autoHide = true,
  hideDelay = 5000
}: ConnectionNotificationProps) {
  const [notifications, setNotifications] = useState<Array<{
    id: string;
    status: HealthStatus;
    timestamp: Date;
    visible: boolean;
  }>>([]);

  useEffect(() => {
    let notificationId = 0;

    const unsubscribe = healthMonitor.onHealthChange((status) => {
      const id = `notification-${++notificationId}`;
      const notification = {
        id,
        status,
        timestamp: new Date(),
        visible: true
      };

      setNotifications(prev => [...prev, notification]);

      if (autoHide) {
        setTimeout(() => {
          setNotifications(prev => 
            prev.map(n => n.id === id ? { ...n, visible: false } : n)
          );
          
          // Remove from array after fade animation
          setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
          }, 300);
        }, hideDelay);
      }
    });

    return unsubscribe;
  }, [autoHide, hideDelay]);

  const dismissNotification = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, visible: false } : n)
    );
    
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 300);
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      default:
        return 'top-4 right-4';
    }
  };

  const getNotificationClasses = (notification: typeof notifications[0]) => {
    const baseClasses = 'mb-2 p-4 rounded-lg shadow-lg border transition-all duration-300 max-w-sm';
    const visibilityClasses = notification.visible 
      ? 'opacity-100 transform translate-x-0' 
      : 'opacity-0 transform translate-x-full';
    
    const statusClasses = notification.status.isHealthy
      ? 'bg-green-50 border-green-200 text-green-800'
      : 'bg-red-50 border-red-200 text-red-800';

    return `${baseClasses} ${visibilityClasses} ${statusClasses}`;
  };

  const getIcon = (isHealthy: boolean) => {
    if (isHealthy) {
      return (
        <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      );
    }

    return (
      <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
    );
  };

  const getTitle = (isHealthy: boolean) => {
    return isHealthy ? 'Connection Restored' : 'Connection Lost';
  };

  const getMessage = (status: HealthStatus) => {
    if (status.isHealthy) {
      return `API connection restored. Response time: ${Math.round(status.responseTime)}ms`;
    }
    return status.error?.userMessage || 'Unable to connect to the API server';
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`fixed z-50 ${getPositionClasses()}`}>
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={getNotificationClasses(notification)}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0">
              {getIcon(notification.status.isHealthy)}
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium">
                {getTitle(notification.status.isHealthy)}
              </h3>
              <p className="mt-1 text-sm opacity-90">
                {getMessage(notification.status)}
              </p>
              <p className="mt-1 text-xs opacity-75">
                {notification.timestamp.toLocaleTimeString()}
              </p>
            </div>
            <div className="ml-4 flex-shrink-0">
              <button
                onClick={() => dismissNotification(notification.id)}
                className="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                <span className="sr-only">Close</span>
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}