/**
 * Error Message System
 * Provides user-friendly error messages with contextual help and troubleshooting suggestions
 * Maps technical errors to actionable user guidance
 */

import { NetworkErrorType, type ClassifiedError } from './error-handling';

export interface ErrorContext {
  operation?: string;
  resource?: string;
  userAction?: string;
  retryCount?: number;
}

export interface ContextualErrorMessage {
  title: string;
  message: string;
  helpText?: string;
}

export interface QuickAction {
  label: string;
  action: string;
  primary?: boolean;
}

export interface SupportInfo {
  documentation?: string;
  contactSupport?: boolean;
  troubleshooting?: string[];
}

export function getContextualErrorMessage(
  error: ClassifiedError,
  context?: ErrorContext
): ContextualErrorMessage {
  const errorType = error.type;
  const operation = context?.operation || 'operation';
  const resource = context?.resource || 'resource';

  switch (errorType) {
    case NetworkErrorType.CONNECTION_TIMEOUT:
      return {
        title: 'Connection Timeout',
        message: `The ${operation} took too long to complete. This might be due to a slow network connection.`,
        helpText: 'Try again or check your internet connection.',
      };

    case NetworkErrorType.SERVER_ERROR:
      return {
        title: 'Server Error',
        message: `We're experiencing technical difficulties with our server. The ${operation} couldn't be completed.`,
        helpText: 'Please try again in a few moments. If the problem persists, contact support.',
      };

    case NetworkErrorType.NETWORK_UNREACHABLE:
      return {
        title: 'Connection Failed',
        message: `Unable to connect to our servers. Please check your internet connection.`,
        helpText: 'Make sure you\'re connected to the internet and try again.',
      };

    case NetworkErrorType.RATE_LIMITED:
      return {
        title: 'Too Many Requests',
        message: `You're making requests too quickly. Please slow down.`,
        helpText: 'Wait a moment before trying again.',
      };

    case NetworkErrorType.SERVICE_UNAVAILABLE:
      return {
        title: 'Service Unavailable',
        message: `The service is temporarily unavailable for maintenance.`,
        helpText: 'Please try again later.',
      };

    case NetworkErrorType.CLIENT_ERROR:
      if (context?.operation === 'file_upload') {
        return {
          title: 'Upload Error',
          message: `There was a problem uploading "${resource}". Please check the file and try again.`,
          helpText: 'Make sure the file is a supported format and under the size limit.',
        };
      }
      return {
        title: 'Request Error',
        message: `There was a problem with your request.`,
        helpText: 'Please check your input and try again.',
      };

    default:
      return {
        title: 'Unexpected Error',
        message: error.userMessage || 'An unexpected error occurred.',
        helpText: 'Please try again or contact support if the problem persists.',
      };
  }
}

export function getQuickActions(
  errorType: NetworkErrorType,
  context?: ErrorContext
): QuickAction[] {
  const actions: QuickAction[] = [];

  switch (errorType) {
    case NetworkErrorType.CONNECTION_TIMEOUT:
    case NetworkErrorType.NETWORK_UNREACHABLE:
      actions.push(
        { label: 'Try Again', action: 'retry', primary: true },
        { label: 'Check Connection', action: 'check_connection' }
      );
      break;

    case NetworkErrorType.SERVER_ERROR:
    case NetworkErrorType.SERVICE_UNAVAILABLE:
      actions.push(
        { label: 'Try Again', action: 'retry', primary: true },
        { label: 'Contact Support', action: 'contact_support' }
      );
      break;

    case NetworkErrorType.RATE_LIMITED:
      actions.push(
        { label: 'Wait and Retry', action: 'wait_retry', primary: true }
      );
      break;

    case NetworkErrorType.CLIENT_ERROR:
      if (context?.operation === 'file_upload') {
        actions.push(
          { label: 'Choose Different File', action: 'change_file', primary: true },
          { label: 'Check File Format', action: 'check_format' }
        );
      } else {
        actions.push(
          { label: 'Fix Input', action: 'fix_input', primary: true },
          { label: 'Try Again', action: 'retry' }
        );
      }
      break;

    default:
      actions.push(
        { label: 'Try Again', action: 'retry', primary: true },
        { label: 'Get Help', action: 'get_help' }
      );
      break;
  }

  return actions;
}

export function getSupportInfo(
  errorType: NetworkErrorType,
  error: ClassifiedError
): SupportInfo {
  const info: SupportInfo = {};

  switch (errorType) {
    case NetworkErrorType.CONNECTION_TIMEOUT:
    case NetworkErrorType.NETWORK_UNREACHABLE:
      info.documentation = '/docs/troubleshooting/connection-issues';
      info.troubleshooting = [
        'Check your internet connection',
        'Try refreshing the page',
        'Disable VPN or proxy temporarily',
        'Try using a different browser',
      ];
      break;

    case NetworkErrorType.SERVER_ERROR:
    case NetworkErrorType.SERVICE_UNAVAILABLE:
      info.contactSupport = true;
      info.troubleshooting = [
        'Wait a few minutes and try again',
        'Check our status page for known issues',
        'Clear browser cache and cookies',
      ];
      break;

    case NetworkErrorType.RATE_LIMITED:
      info.documentation = '/docs/api/rate-limits';
      info.troubleshooting = [
        'Wait before making another request',
        'Reduce the frequency of your requests',
        'Consider upgrading your plan for higher limits',
      ];
      break;

    case NetworkErrorType.CLIENT_ERROR:
      info.documentation = '/docs/api/errors';
      info.troubleshooting = [
        'Check the format of your request',
        'Verify required fields are filled',
        'Ensure file types are supported',
      ];
      break;

    default:
      info.contactSupport = true;
      info.documentation = '/docs/support';
      break;
  }

  return info;
}
