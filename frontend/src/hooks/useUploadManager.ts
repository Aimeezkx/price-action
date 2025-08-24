/**
 * Upload Manager Hook
 * React hook for managing file uploads with progress tracking
 * Integrates with the upload manager and error notification system
 */

import { useState, useEffect, useCallback } from 'react';
import { uploadManager, UploadItem, UploadOptions, UploadStats } from '../lib/upload-manager';
import { useUploadErrorHandler } from './useErrorNotifications';

export interface UseUploadManagerReturn {
  uploads: UploadItem[];
  activeUploads: UploadItem[];
  stats: UploadStats;
  addUpload: (file: File, options?: UploadOptions) => string;
  cancelUpload: (id: string) => boolean;
  retryUpload: (id: string) => Promise<any>;
  clearCompleted: () => void;
  clearAll: () => void;
  getUpload: (id: string) => UploadItem | undefined;
}

export const useUploadManager = (): UseUploadManagerReturn => {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [stats, setStats] = useState<UploadStats>(uploadManager.getUploadStats());
  const { handleUploadError } = useUploadErrorHandler();

  // Update state when uploads change
  const updateState = useCallback(() => {
    setUploads(uploadManager.getAllUploads());
    setStats(uploadManager.getUploadStats());
  }, []);

  // Set up polling for upload updates
  useEffect(() => {
    const interval = setInterval(updateState, 500);
    return () => clearInterval(interval);
  }, [updateState]);

  const addUpload = useCallback((file: File, options: UploadOptions = {}): string => {
    const enhancedOptions: UploadOptions = {
      ...options,
      onProgress: (item: UploadItem) => {
        updateState();
        options.onProgress?.(item);
      },
      onStatusChange: (item: UploadItem) => {
        updateState();
        options.onStatusChange?.(item);
      },
      onComplete: (item: UploadItem, result: any) => {
        updateState();
        options.onComplete?.(item, result);
      },
      onError: (item: UploadItem, error) => {
        updateState();
        
        // Show error notification
        handleUploadError(
          new Error(error.userMessage),
          item.file.name,
          () => retryUpload(item.id)
        );
        
        options.onError?.(item, error);
      }
    };

    const id = uploadManager.addUpload(file, enhancedOptions);
    updateState();
    return id;
  }, [handleUploadError, updateState]);

  const cancelUpload = useCallback((id: string): boolean => {
    const result = uploadManager.cancelUpload(id);
    updateState();
    return result;
  }, [updateState]);

  const retryUpload = useCallback(async (id: string): Promise<any> => {
    try {
      const result = await uploadManager.retryUpload(id);
      updateState();
      return result;
    } catch (error) {
      updateState();
      throw error;
    }
  }, [updateState]);

  const clearCompleted = useCallback(() => {
    uploadManager.clearCompleted();
    updateState();
  }, [updateState]);

  const clearAll = useCallback(() => {
    uploadManager.clearAll();
    updateState();
  }, [updateState]);

  const getUpload = useCallback((id: string): UploadItem | undefined => {
    return uploadManager.getUpload(id);
  }, []);

  const activeUploads = uploads.filter(upload => 
    ['preparing', 'uploading', 'processing'].includes(upload.status)
  );

  return {
    uploads,
    activeUploads,
    stats,
    addUpload,
    cancelUpload,
    retryUpload,
    clearCompleted,
    clearAll,
    getUpload
  };
};

// Specialized hook for single file uploads
export const useSingleUpload = () => {
  const { addUpload, getUpload, cancelUpload, retryUpload } = useUploadManager();
  const [currentUploadId, setCurrentUploadId] = useState<string | null>(null);

  const startUpload = useCallback((file: File, options?: UploadOptions) => {
    // Cancel any existing upload
    if (currentUploadId) {
      cancelUpload(currentUploadId);
    }

    const id = addUpload(file, {
      ...options,
      onComplete: (item, result) => {
        setCurrentUploadId(null);
        options?.onComplete?.(item, result);
      },
      onError: (item, error) => {
        // Don't clear currentUploadId on error to allow retry
        options?.onError?.(item, error);
      }
    });

    setCurrentUploadId(id);
    return id;
  }, [addUpload, cancelUpload, currentUploadId]);

  const cancel = useCallback(() => {
    if (currentUploadId) {
      cancelUpload(currentUploadId);
      setCurrentUploadId(null);
    }
  }, [cancelUpload, currentUploadId]);

  const retry = useCallback(() => {
    if (currentUploadId) {
      return retryUpload(currentUploadId);
    }
    return Promise.reject(new Error('No upload to retry'));
  }, [retryUpload, currentUploadId]);

  const currentUpload = currentUploadId ? getUpload(currentUploadId) : null;

  return {
    currentUpload,
    startUpload,
    cancel,
    retry,
    isUploading: currentUpload?.status === 'uploading' || currentUpload?.status === 'processing'
  };
};