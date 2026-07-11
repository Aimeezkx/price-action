/**
 * Upload Manager
 * Manages file uploads with detailed progress tracking and error handling
 * Provides upload queue management and retry functionality
 */

import { UploadStatus } from '../components/UploadProgress';
import { classifyError, ClassifiedError } from './error-handling';

export interface UploadItem {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  uploadSpeed?: number;
  timeRemaining?: number;
  startTime?: Date;
  endTime?: Date;
  error?: ClassifiedError;
  retryCount: number;
  maxRetries: number;
}

export interface UploadOptions {
  maxRetries?: number;
  chunkSize?: number;
  timeout?: number;
  onProgress?: (item: UploadItem) => void;
  onStatusChange?: (item: UploadItem) => void;
  onComplete?: (item: UploadItem, result: any) => void;
  onError?: (item: UploadItem, error: ClassifiedError) => void;
}

export interface UploadStats {
  totalUploads: number;
  activeUploads: number;
  completedUploads: number;
  failedUploads: number;
  totalBytes: number;
  uploadedBytes: number;
  averageSpeed: number;
}

export class UploadManager {
  private uploads: Map<string, UploadItem> = new Map();
  private activeUploads: Set<string> = new Set();
  private maxConcurrentUploads = 3;
  private uploadQueue: string[] = [];
  private abortControllers: Map<string, AbortController> = new Map();

  public addUpload(file: File, options: UploadOptions = {}): string {
    const id = this.generateUploadId();

    const uploadItem: UploadItem = {
      id,
      file,
      status: 'idle',
      progress: 0,
      retryCount: 0,
      maxRetries: options.maxRetries || 3
    };

    this.uploads.set(id, uploadItem);
    this.uploadQueue.push(id);

    // Start upload if we have capacity
    this.processQueue();

    return id;
  }

  public async startUpload(id: string, options: UploadOptions = {}): Promise<any> {
    const uploadItem = this.uploads.get(id);
    if (!uploadItem) {
      throw new Error(`Upload ${id} not found`);
    }

    if (this.activeUploads.has(id)) {
      throw new Error(`Upload ${id} is already in progress`);
    }

    try {
      this.activeUploads.add(id);
      this.updateUploadStatus(id, 'preparing');

      const result = await this.performUpload(uploadItem, options);

      this.updateUploadStatus(id, 'success');
      uploadItem.endTime = new Date();

      options.onComplete?.(uploadItem, result);
      return result;

    } catch (error) {
      const classifiedError = classifyError(error as Error);
      uploadItem.error = classifiedError;

      if (uploadItem.retryCount < uploadItem.maxRetries && classifiedError.isRetryable) {
        uploadItem.retryCount++;
        this.updateUploadStatus(id, 'idle');
        // Add back to queue for retry
        this.uploadQueue.push(id);
      } else {
        this.updateUploadStatus(id, 'failed');
        uploadItem.endTime = new Date();
        options.onError?.(uploadItem, classifiedError);
      }

      throw error;
    } finally {
      this.activeUploads.delete(id);
      this.abortControllers.delete(id);
      this.processQueue();
    }
  }

  public cancelUpload(id: string): boolean {
    const uploadItem = this.uploads.get(id);
    if (!uploadItem) return false;

    const abortController = this.abortControllers.get(id);
    if (abortController) {
      abortController.abort();
    }

    this.updateUploadStatus(id, 'cancelled');
    this.activeUploads.delete(id);

    // Remove from queue if it's there
    const queueIndex = this.uploadQueue.indexOf(id);
    if (queueIndex > -1) {
      this.uploadQueue.splice(queueIndex, 1);
    }

    this.processQueue();
    return true;
  }

  public retryUpload(id: string, options: UploadOptions = {}): Promise<any> {
    const uploadItem = this.uploads.get(id);
    if (!uploadItem) {
      throw new Error(`Upload ${id} not found`);
    }

    if (uploadItem.status !== 'failed') {
      throw new Error(`Upload ${id} is not in a failed state`);
    }

    uploadItem.retryCount++;
    uploadItem.error = undefined;
    this.updateUploadStatus(id, 'idle');

    // Add to front of queue for immediate retry
    this.uploadQueue.unshift(id);
    this.processQueue();

    return this.startUpload(id, options);
  }

  public getUpload(id: string): UploadItem | undefined {
    return this.uploads.get(id);
  }

  public getAllUploads(): UploadItem[] {
    return Array.from(this.uploads.values());
  }

  public getActiveUploads(): UploadItem[] {
    return Array.from(this.activeUploads)
      .map(id => this.uploads.get(id))
      .filter(Boolean) as UploadItem[];
  }

  public getUploadStats(): UploadStats {
    const uploads = this.getAllUploads();
    const totalBytes = uploads.reduce((sum, upload) => sum + upload.file.size, 0);
    const uploadedBytes = uploads.reduce((sum, upload) => {
      return sum + (upload.file.size * upload.progress / 100);
    }, 0);

    const completedUploads = uploads.filter(u => u.status === 'success');
    const averageSpeed = completedUploads.length > 0
      ? completedUploads.reduce((sum, upload) => {
          if (upload.startTime && upload.endTime) {
            const duration = (upload.endTime.getTime() - upload.startTime.getTime()) / 1000;
            return sum + (upload.file.size / duration);
          }
          return sum;
        }, 0) / completedUploads.length
      : 0;

    return {
      totalUploads: uploads.length,
      activeUploads: this.activeUploads.size,
      completedUploads: uploads.filter(u => u.status === 'success').length,
      failedUploads: uploads.filter(u => u.status === 'failed').length,
      totalBytes,
      uploadedBytes,
      averageSpeed
    };
  }

  public clearCompleted(): void {
    const toRemove: string[] = [];

    this.uploads.forEach((upload, id) => {
      if (upload.status === 'success' || upload.status === 'cancelled') {
        toRemove.push(id);
      }
    });

    toRemove.forEach(id => {
      this.uploads.delete(id);
    });
  }

  public clearAll(): void {
    // Cancel all active uploads
    this.activeUploads.forEach(id => {
      this.cancelUpload(id);
    });

    this.uploads.clear();
    this.uploadQueue = [];
    this.abortControllers.clear();
  }

  private async performUpload(uploadItem: UploadItem, options: UploadOptions): Promise<any> {
    const abortController = new AbortController();
    this.abortControllers.set(uploadItem.id, abortController);

    uploadItem.startTime = new Date();
    this.updateUploadStatus(uploadItem.id, 'uploading');

    // Create FormData
    const formData = new FormData();
    formData.append('file', uploadItem.file);

    // Track upload progress
    const startTime = Date.now();
    let lastProgressTime = startTime;
    let lastUploadedBytes = 0;

    const updateProgress = (loaded: number, total: number) => {
      const progress = (loaded / total) * 100;
      const currentTime = Date.now();
      const timeDiff = (currentTime - lastProgressTime) / 1000;

      if (timeDiff > 0.5) { // Update speed calculation every 500ms
        const bytesDiff = loaded - lastUploadedBytes;
        const speed = bytesDiff / timeDiff;
        const remaining = (total - loaded) / speed;

        uploadItem.progress = progress;
        uploadItem.uploadSpeed = speed;
        uploadItem.timeRemaining = remaining;

        lastProgressTime = currentTime;
        lastUploadedBytes = loaded;

        options.onProgress?.(uploadItem);
      }
    };

    try {
      // Use XMLHttpRequest for progress tracking
      const result = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            updateProgress(event.loaded, event.total);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch (e) {
              resolve(xhr.responseText);
            }
          } else {
            reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error occurred'));
        });

        xhr.addEventListener('timeout', () => {
          reject(new Error('Upload timeout'));
        });

        abortController.signal.addEventListener('abort', () => {
          xhr.abort();
          reject(new Error('Upload cancelled'));
        });

        xhr.open('POST', '/api/documents/upload');
        xhr.timeout = options.timeout || 300000; // 5 minutes default
        xhr.send(formData);
      });

      // Simulate processing phase
      this.updateUploadStatus(uploadItem.id, 'processing');
      uploadItem.progress = 100;
      options.onProgress?.(uploadItem);

      return result;

    } catch (error) {
      throw error;
    }
  }

  private processQueue(): void {
    while (
      this.uploadQueue.length > 0 &&
      this.activeUploads.size < this.maxConcurrentUploads
    ) {
      const id = this.uploadQueue.shift();
      if (id) {
        const uploadItem = this.uploads.get(id);
        if (uploadItem && uploadItem.status === 'idle') {
          // Start upload asynchronously
          this.startUpload(id).catch(() => {
            // Error handling is done in startUpload
          });
        }
      }
    }
  }

  private updateUploadStatus(id: string, status: UploadStatus): void {
    const uploadItem = this.uploads.get(id);
    if (uploadItem) {
      uploadItem.status = status;
      // Notify listeners if needed
    }
  }

  private generateUploadId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  public setMaxConcurrentUploads(max: number): void {
    this.maxConcurrentUploads = Math.max(1, max);
    this.processQueue();
  }
}

// Export singleton instance
export const uploadManager = new UploadManager();