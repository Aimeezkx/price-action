/**
 * Error Notification Container
 * Manages and displays multiple error notifications
 * Provides centralized notification display with proper positioning and animations
 */

import React from 'react';
import { useErrorNotifications } from '../hooks/useErrorNotifications';
import ErrorNotification from './ErrorNotification';

export interface ErrorNotificationContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  maxVisible?: number;
  className?: string;
}

export const ErrorNotificationContainer: React.FC<ErrorNotificationContainerProps> = ({
  position = 'top-right',
  maxVisible = 5,
  className = ''
}) => {
  const { 
    notifications, 
    dismissNotification, 
    retryNotification,
    stats 
  } = useErrorNotifications();

  const handleAction = (action: string, id: string) => {
    switch (action) {
      case 'check_connection':
        // Could implement network diagnostics
        console.log('Checking connection...');
        break;
      case 'contact_support':
        // Could open support modal or copy debug info
        console.log('Contacting support...');
        break;
      default:
        console.log(`Action ${action} for notification ${id}`);
    }
  };

  const getPositionStyles = (position: string): string => {
    switch (position) {
      case 'top-right':
        return 'fixed top-4 right-4 z-50';
      case 'top-left':
        return 'fixed top-4 left-4 z-50';
      case 'bottom-right':
        return 'fixed bottom-4 right-4 z-50';
      case 'bottom-left':
        return 'fixed bottom-4 left-4 z-50';
      case 'top-center':
        return 'fixed top-4 left-1/2 transform -translate-x-1/2 z-50';
      case 'bottom-center':
        return 'fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50';
      default:
        return 'fixed top-4 right-4 z-50';
    }
  };

  const visibleNotifications = notifications.slice(0, maxVisible);
  const hiddenCount = Math.max(0, notifications.length - maxVisible);

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`${getPositionStyles(position)} ${className}`}>
      <div className="flex flex-col space-y-2 max-w-md">
        {/* Notification Stats (for debugging/development) */}
        {process.env.NODE_ENV === 'development' && stats.active > 0 && (
          <div className="text-xs text-gray-500 bg-gray-100 p-2 rounded">
            Active: {stats.active} | Total: {stats.total}
          </div>
        )}

        {/* Visible Notifications */}
        {visibleNotifications.map((notification) => (
          <div
            key={notification.id}
            className="animate-slide-in-right"
            style={{
              animation: 'slideInRight 0.3s ease-out'
            }}
          >
            <ErrorNotification
              notification={notification}
              onRetry={retryNotification}
              onDismiss={dismissNotification}
              onAction={handleAction}
            />
          </div>
        ))}

        {/* Hidden Notifications Indicator */}
        {hiddenCount > 0 && (
          <div className="bg-gray-100 border border-gray-300 rounded-lg p-3 text-center text-sm text-gray-600">
            <p>+ {hiddenCount} more notification{hiddenCount > 1 ? 's' : ''}</p>
            <button
              onClick={() => {
                // Could implement a "show all" modal or expand functionality
                console.log('Show all notifications');
              }}
              className="mt-1 text-blue-600 hover:text-blue-800 text-xs underline"
            >
              Show All
            </button>
          </div>
        )}
      </div>

      {/* Custom CSS for animations */}
      <style jsx>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        @keyframes slideOutRight {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(100%);
            opacity: 0;
          }
        }

        .animate-slide-in-right {
          animation: slideInRight 0.3s ease-out;
        }

        .animate-slide-out-right {
          animation: slideOutRight 0.3s ease-in;
        }
      `}</style>
    </div>
  );
};

export default ErrorNotificationContainer;