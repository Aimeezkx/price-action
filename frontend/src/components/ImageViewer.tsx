import React, { useState, useEffect } from 'react';
import type { Figure } from '../types';

interface ImageViewerProps {
  figure: Figure;
  onClose: () => void;
}

export function ImageViewer({ figure, onClose }: ImageViewerProps) {
  const [isZoomed, setIsZoomed] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75"
      onClick={handleBackdropClick}
    >
      <div className="relative max-w-7xl max-h-full mx-4 bg-white rounded-lg shadow-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              Figure from Page {figure.page_number}
            </h3>
            {figure.caption && (
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {figure.caption}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            {/* Zoom Toggle */}
            <button
              onClick={() => setIsZoomed(!isZoomed)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
              title={isZoomed ? 'Zoom out' : 'Zoom in'}
            >
              {isZoomed ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10h-3" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
              )}
            </button>
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
              title="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Image Container */}
        <div className={`
          relative overflow-auto
          ${isZoomed ? 'max-h-[80vh]' : 'max-h-[70vh]'}
        `}>
          {!imageError ? (
            <img
              src={`/api/files/${figure.image_path}`}
              alt={figure.caption || 'Figure'}
              className={`
                block mx-auto
                ${isZoomed ? 'max-w-none' : 'max-w-full max-h-full object-contain'}
              `}
              style={isZoomed ? { width: 'auto', height: 'auto' } : {}}
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-lg font-medium">Image not available</p>
              <p className="text-sm text-gray-400 mt-1">The image file could not be loaded</p>
            </div>
          )}
        </div>

        {/* Caption (if available and not shown in header) */}
        {figure.caption && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Caption</h4>
            <p className="text-sm text-gray-700 leading-relaxed">
              {figure.caption}
            </p>
            
            {/* Image metadata */}
            <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-500">
              <span>Page {figure.page_number}</span>
              {figure.bbox && (
                <span>
                  Position: {Math.round(figure.bbox.x)}, {Math.round(figure.bbox.y)}
                </span>
              )}
              {figure.bbox && (
                <span>
                  Size: {Math.round(figure.bbox.width)} × {Math.round(figure.bbox.height)}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Mobile-friendly controls */}
        <div className="md:hidden p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setIsZoomed(!isZoomed)}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              {isZoomed ? 'Zoom Out' : 'Zoom In'}
            </button>
            <button
              onClick={onClose}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}