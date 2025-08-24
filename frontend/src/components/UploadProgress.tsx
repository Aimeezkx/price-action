/**
 * Enhanced Upload Progress Component
 * Provides detailed upload progress tracking with visual feedback
 * Includes upload status indicators (uploading, success, failed)
 */

import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

export type UploadStatus = 'idle' | 'preparing' | 'uploading' | 'processing' | 'success' | 'failed' | 'cancelled';

export interface UploadProgressProps {
  status: UploadStatus;
  progress: number; // 0-100
  fileName?: string;
  fileSize?: number;
  uploadSpeed?: number; // bytes per second
  timeRemaining?: number; // seconds
  error?: string;
  onCancel?: () => void;
  onRetry?: () => void;
  className?: string;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  status,
  progress,
  fileName,
  fileSize,
  uploadSpeed,
  timeRemaining,
  error,
  onCancel,
  onRetry,
  className = ''
}) => {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatSpeed = (bytesPerSecond: number): string => {
    return `${formatFileSize(bytesPerSecond)}/s`;
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getStatusIcon = (status: UploadStatus): React.ReactNode => {
    switch (status) {
      case 'preparing':
        return <LoadingSpinner size="sm" className="text-blue-500" />;
      case 'uploading':
        return <LoadingSpinner size="sm" className="text-blue-500" />;
      case 'processing':
        return <LoadingSpinner size="sm" className="text-yellow-500" />;
      case 'success':
        return (
          <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'failed':
        return (
          <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'cancelled':
        return (
          <div className="w-5 h-5 bg-gray-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusText = (status: UploadStatus): string => {
    switch (status) {
      case 'preparing':
        return 'Preparing upload...';
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing document...';
      case 'success':
        return 'Upload completed successfully';
      case 'failed':
        return error || 'Upload failed';
      case 'cancelled':
        return 'Upload cancelled';
      default:
        return '';
    }
  };

  const getProgressBarColor = (status: UploadStatus): string => {
    switch (status) {
      case 'uploading':
        return 'bg-blue-500';
      case 'processing':
        return 'bg-yellow-500';
      case 'success':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'cancelled':
        return 'bg-gray-500';
      default:
        return 'bg-blue-500';
    }
  };

  const isActive = ['preparing', 'uploading', 'processing'].includes(status);
  const isComplete = ['success', 'failed', 'cancelled'].includes(status);

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 shadow-sm ${className}`}>
      <div className="flex items-start space-x-3">
        {/* Status Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {getStatusIcon(status)}
        </div>

        {/* Upload Details */}
        <div className="flex-1 min-w-0">
          {/* File Name */}
          {fileName && (
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-900 truncate">
                {fileName}
              </p>
              {fileSize && (
                <span className="text-xs text-gray-500 ml-2">
                  {formatFileSize(fileSize)}
                </span>
              )}
            </div>
          )}

          {/* Status Text */}
          <p className={`text-sm mt-1 ${
            status === 'failed' ? 'text-red-600' : 
            status === 'success' ? 'text-green-600' : 
            'text-gray-600'
          }`}>
            {getStatusText(status)}
          </p>

          {/* Progress Bar */}
          {(isActive || isComplete) && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>{Math.round(progress)}% complete</span>
                {uploadSpeed && timeRemaining && status === 'uploading' && (
                  <span>
                    {formatSpeed(uploadSpeed)} • {formatTime(timeRemaining)} remaining
                  </span>
                )}
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(status)}`}
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                />
              </div>
            </div>
          )}

          {/* Upload Statistics */}
          {status === 'uploading' && (uploadSpeed || timeRemaining) && (
            <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
              {uploadSpeed && (
                <span>Speed: {formatSpeed(uploadSpeed)}</span>
              )}
              {timeRemaining && (
                <span>Time remaining: {formatTime(timeRemaining)}</span>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-3 flex items-center space-x-2">
            {isActive && onCancel && (
              <button
                onClick={onCancel}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
            )}

            {status === 'failed' && onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Retry Upload
              </button>
            )}

            {status === 'success' && (
              <span className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-green-700">
                ✓ Upload successful
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadProgress;