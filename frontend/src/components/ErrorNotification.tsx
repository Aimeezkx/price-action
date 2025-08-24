/**
 * Enhanced Error Notification Component
 * Displays user-friendly error messages with contextual help and retry options
 * Integrates with the error classification and notification management systems
 */

import React, { useState } from 'react';
import { ErrorNotificationState } from '../lib/error-notification-manager';
import { getContextualErrorMessage, getQuickActions, getSupportInfo } from '../lib/error-messages';
import { NetworkErrorType } from '../lib/error-handling';

export interface ErrorNotificationProps {
  notification: ErrorNotificationState;
  onRetry?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onAction?: (action: string, id: string) => void;
  className?: string;
}

export const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  notification,
  onRetry,
  onDismiss,
  onAction,
  className = ''
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);

  const { error, options, id, retryCount } = notification;
  const contextualMessage = getContextualErrorMessage(error, options.context);
  const quickActions = getQuickActions(error.type, options.context);
  const supportInfo = getSupportInfo(error.type, error);

  const handleDismiss = () => {
    onDismiss?.(id);
  };

  const handleRetry = () => {
    onRetry?.(id);
  };

  const handleAction = (action: string) => {
    switch (action) {
      case 'retry':
        handleRetry();
        break;
      case 'dismiss':
        handleDismiss();
        break;
      case 'check_connection':
        // Open network diagnostics or connection check
        onAction?.(action, id);
        break;
      case 'refresh':
        window.location.reload();
        break;
      case 'contact_support':
        // Open support contact form or copy debug info
        onAction?.(action, id);
        break;
      case 'wait_retry':
        // Implement delayed retry
        setTimeout(() => handleRetry(), 5000);
        break;
      default:
        onAction?.(action, id);
    }
  };

  const getErrorIcon = (errorType: NetworkErrorType): string => {
    switch (errorType) {
      case NetworkErrorType.CONNECTION_TIMEOUT:
        return '⏱️';
      case NetworkErrorType.SERVER_ERROR:
        return '🔧';
      case NetworkErrorType.NETWORK_UNREACHABLE:
        return '🌐';
      case NetworkErrorType.DNS_RESOLUTION_FAILED:
        return '🔍';
      case NetworkErrorType.CORS_ERROR:
        return '🔒';
      case NetworkErrorType.RATE_LIMITED:
        return '⏳';
      case NetworkErrorType.SERVICE_UNAVAILABLE:
        return '🚧';
      case NetworkErrorType.CLIENT_ERROR:
        return '❌';
      default:
        return '⚠️';
    }
  };

  const getSeverityStyles = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 border-red-300 text-red-900';
      case 'high':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'low':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getButtonStyles = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 hover:bg-red-200 text-red-700 border-red-300';
      case 'high':
        return 'bg-red-100 hover:bg-red-200 text-red-700 border-red-300';
      case 'medium':
        return 'bg-yellow-100 hover:bg-yellow-200 text-yellow-700 border-yellow-300';
      case 'low':
        return 'bg-blue-100 hover:bg-blue-200 text-blue-700 border-blue-300';
      default:
        return 'bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300';
    }
  };

  const severity = contextualMessage.severity;
  const severityStyles = getSeverityStyles(severity);
  const buttonStyles = getButtonStyles(severity);

  return (
    <div className={`max-w-md mb-4 ${className}`}>
      <div className={`rounded-lg border p-4 shadow-lg transition-all duration-300 ${severityStyles}`}>
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <span className="text-2xl" role="img" aria-label="Error icon">
              {getErrorIcon(error.type)}
            </span>
          </div>
          
          <div className="ml-3 flex-1">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">
                {contextualMessage.title}
                {retryCount > 0 && (
                  <span className="ml-2 text-xs opacity-75">
                    (Attempt #{retryCount + 1})
                  </span>
                )}
              </h3>
              <button
                onClick={handleDismiss}
                className="ml-2 inline-flex text-sm hover:opacity-75 transition-opacity"
                aria-label="Dismiss notification"
              >
                ✕
              </button>
            </div>
            
            <div className="mt-2 text-sm">
              <p>{contextualMessage.message}</p>
              {contextualMessage.helpText && (
                <p className="mt-1 text-xs opacity-75">{contextualMessage.helpText}</p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="mt-3 flex flex-wrap gap-2">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleAction(action.action)}
                  className={`inline-flex items-center px-3 py-1.5 border rounded-md text-xs font-medium transition-colors ${
                    action.primary ? buttonStyles : `${buttonStyles} opacity-75`
                  }`}
                >
                  {action.label}
                </button>
              ))}
              
              {contextualMessage.troubleshootingSteps.length > 0 && (
                <button
                  onClick={() => setShowTroubleshooting(!showTroubleshooting)}
                  className={`inline-flex items-center px-3 py-1.5 border rounded-md text-xs font-medium transition-colors ${buttonStyles} opacity-75`}
                >
                  {showTroubleshooting ? '📋 Hide Help' : '🔧 Troubleshoot'}
                </button>
              )}

              {options.showTechnicalDetails && (
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className={`inline-flex items-center px-3 py-1.5 border rounded-md text-xs font-medium transition-colors ${buttonStyles} opacity-75`}
                >
                  {showDetails ? '📋 Hide Details' : '🔍 Show Details'}
                </button>
              )}
            </div>

            {/* Troubleshooting Steps */}
            {showTroubleshooting && (
              <div className="mt-3 p-3 bg-black bg-opacity-5 rounded text-xs">
                <h4 className="font-medium mb-2">Troubleshooting Steps:</h4>
                <ol className="list-decimal list-inside space-y-1">
                  {contextualMessage.troubleshootingSteps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
                
                {contextualMessage.preventionTips && contextualMessage.preventionTips.length > 0 && (
                  <div className="mt-2">
                    <h5 className="font-medium mb-1">Prevention Tips:</h5>
                    <ul className="list-disc list-inside space-y-1">
                      {contextualMessage.preventionTips.map((tip, index) => (
                        <li key={index}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Technical Details */}
            {showDetails && options.showTechnicalDetails && (
              <div className="mt-3 p-3 bg-black bg-opacity-10 rounded text-xs font-mono">
                <h4 className="font-medium mb-2">Technical Details:</h4>
                <div className="space-y-1">
                  <p><strong>Error Type:</strong> {error.type}</p>
                  <p><strong>Request ID:</strong> {error.requestId}</p>
                  <p><strong>Time:</strong> {error.timestamp.toLocaleString()}</p>
                  {error.statusCode && (
                    <p><strong>Status Code:</strong> {error.statusCode}</p>
                  )}
                  <p><strong>Technical:</strong> {error.technicalMessage}</p>
                  {options.context && (
                    <div className="mt-2">
                      <p><strong>Context:</strong></p>
                      <pre className="text-xs">{JSON.stringify(options.context, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Support Information */}
            {supportInfo.shouldContactSupport && (
              <div className="mt-3 p-2 bg-black bg-opacity-5 rounded text-xs">
                <p className="font-medium text-red-700">⚠️ {supportInfo.supportMessage}</p>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(supportInfo.debugInfo, null, 2));
                    // Could show a toast here
                  }}
                  className="mt-1 text-blue-600 hover:text-blue-800 underline"
                >
                  📋 Copy Debug Info
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorNotification;