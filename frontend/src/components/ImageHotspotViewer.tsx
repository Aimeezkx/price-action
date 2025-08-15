import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import type { Hotspot } from '../types';

interface ImageHotspotViewerProps {
  imageSrc: string;
  hotspots: Hotspot[];
  mode: 'study' | 'answer'; // study = clickable, answer = show all
  onHotspotClick?: (hotspot: Hotspot) => void;
  onValidationComplete?: (correct: boolean, clickedHotspots: Hotspot[]) => void;
  className?: string;
  maxZoom?: number;
  minZoom?: number;
  zoomStep?: number;
  enableKeyboardControls?: boolean;
}

export function ImageHotspotViewer({
  imageSrc,
  hotspots,
  mode,
  onHotspotClick,
  onValidationComplete,
  className = '',
  maxZoom = 4,
  minZoom = 0.5,
  zoomStep = 1.2,
  enableKeyboardControls = true
}: ImageHotspotViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  
  // Zoom and pan state
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  // Hotspot interaction state
  const [clickedHotspots, setClickedHotspots] = useState<Set<string>>(new Set());
  const [hoveredHotspot, setHoveredHotspot] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'success' | 'partial' | 'error'>('success');
  
  // Touch gesture state
  const [touches, setTouches] = useState<TouchList | null>(null);
  const [lastTouchDistance, setLastTouchDistance] = useState(0);
  const [lastTouchCenter, setLastTouchCenter] = useState({ x: 0, y: 0 });
  
  // Performance optimization
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Memoized calculations
  const correctHotspots = useMemo(() => 
    hotspots.filter(h => h.correct), 
    [hotspots]
  );
  
  const containerBounds = useMemo(() => {
    if (!containerRef.current) return { width: 0, height: 0 };
    const rect = containerRef.current.getBoundingClientRect();
    return { width: rect.width, height: rect.height };
  }, [imageLoaded]);

  // Reset state when mode changes
  useEffect(() => {
    if (mode === 'study') {
      setClickedHotspots(new Set());
      setShowFeedback(false);
      setFeedbackType('success');
    }
  }, [mode]);

  // Handle image load
  const handleImageLoad = useCallback(() => {
    if (imageRef.current) {
      setImageDimensions({
        width: imageRef.current.naturalWidth,
        height: imageRef.current.naturalHeight
      });
      setImageLoaded(true);
    }
  }, []);

  // Calculate distance between two touches
  const getTouchDistance = useCallback((touches: TouchList) => {
    if (touches.length < 2) return 0;
    const touch1 = touches[0];
    const touch2 = touches[1];
    return Math.sqrt(
      Math.pow(touch2.clientX - touch1.clientX, 2) +
      Math.pow(touch2.clientY - touch1.clientY, 2)
    );
  }, []);

  // Calculate center point between two touches
  const getTouchCenter = useCallback((touches: TouchList) => {
    if (touches.length < 2) return { x: 0, y: 0 };
    const touch1 = touches[0];
    const touch2 = touches[1];
    return {
      x: (touch1.clientX + touch2.clientX) / 2,
      y: (touch1.clientY + touch2.clientY) / 2
    };
  }, []);

  // Constrain position to prevent image from going out of bounds
  const constrainPosition = useCallback((newPosition: { x: number; y: number }, currentScale: number) => {
    if (!containerRef.current || !imageRef.current) return newPosition;
    
    const container = containerRef.current.getBoundingClientRect();
    const imageRect = imageRef.current.getBoundingClientRect();
    
    const scaledWidth = imageRect.width * currentScale;
    const scaledHeight = imageRect.height * currentScale;
    
    const maxX = Math.max(0, (scaledWidth - container.width) / 2);
    const maxY = Math.max(0, (scaledHeight - container.height) / 2);
    
    return {
      x: Math.max(-maxX, Math.min(maxX, newPosition.x)),
      y: Math.max(-maxY, Math.min(maxY, newPosition.y))
    };
  }, []);

  // Handle zoom controls
  const handleZoomIn = useCallback(() => {
    setIsTransitioning(true);
    setScale(prev => {
      const newScale = Math.min(prev * zoomStep, maxZoom);
      setPosition(current => constrainPosition(current, newScale));
      return newScale;
    });
    setTimeout(() => setIsTransitioning(false), 200);
  }, [zoomStep, maxZoom, constrainPosition]);

  const handleZoomOut = useCallback(() => {
    setIsTransitioning(true);
    setScale(prev => {
      const newScale = Math.max(prev / zoomStep, minZoom);
      if (newScale <= 1) {
        setPosition({ x: 0, y: 0 });
      } else {
        setPosition(current => constrainPosition(current, newScale));
      }
      return newScale;
    });
    setTimeout(() => setIsTransitioning(false), 200);
  }, [zoomStep, minZoom, constrainPosition]);

  const handleResetView = useCallback(() => {
    setIsTransitioning(true);
    setScale(1);
    setPosition({ x: 0, y: 0 });
    setTimeout(() => setIsTransitioning(false), 200);
  }, []);

  // Handle zoom to specific scale
  const handleZoomTo = useCallback((targetScale: number, centerPoint?: { x: number; y: number }) => {
    setIsTransitioning(true);
    const newScale = Math.max(minZoom, Math.min(maxZoom, targetScale));
    
    if (centerPoint && containerRef.current) {
      const container = containerRef.current.getBoundingClientRect();
      const centerX = centerPoint.x - container.left - container.width / 2;
      const centerY = centerPoint.y - container.top - container.height / 2;
      
      const newPosition = {
        x: -centerX * (newScale - 1),
        y: -centerY * (newScale - 1)
      };
      
      setPosition(constrainPosition(newPosition, newScale));
    } else if (newScale <= 1) {
      setPosition({ x: 0, y: 0 });
    }
    
    setScale(newScale);
    setTimeout(() => setIsTransitioning(false), 200);
  }, [minZoom, maxZoom, constrainPosition]);

  // Handle mouse wheel zoom
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? (1 / zoomStep) : zoomStep;
    const rect = containerRef.current?.getBoundingClientRect();
    
    if (rect) {
      const centerPoint = {
        x: e.clientX,
        y: e.clientY
      };
      
      const newScale = Math.max(minZoom, Math.min(maxZoom, scale * delta));
      handleZoomTo(newScale, centerPoint);
    }
  }, [scale, zoomStep, minZoom, maxZoom, handleZoomTo]);

  // Handle mouse drag
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (scale > 1) {
      e.preventDefault();
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  }, [scale, position]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging && scale > 1) {
      const newPosition = {
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      };
      setPosition(constrainPosition(newPosition, scale));
    }
  }, [isDragging, dragStart, scale, constrainPosition]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Handle double-click to zoom
  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const centerPoint = { x: e.clientX, y: e.clientY };
    
    if (scale > 1) {
      handleZoomTo(1);
    } else {
      handleZoomTo(2, centerPoint);
    }
  }, [scale, handleZoomTo]);

  // Handle touch gestures
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touchList = e.touches;
    setTouches(touchList);
    
    if (touchList.length === 2) {
      e.preventDefault();
      setLastTouchDistance(getTouchDistance(touchList));
      setLastTouchCenter(getTouchCenter(touchList));
    } else if (touchList.length === 1 && scale > 1) {
      setIsDragging(true);
      setDragStart({
        x: touchList[0].clientX - position.x,
        y: touchList[0].clientY - position.y
      });
    }
  }, [scale, position, getTouchDistance, getTouchCenter]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const touchList = e.touches;
    
    if (touchList.length === 2 && touches && touches.length === 2) {
      e.preventDefault();
      
      // Pinch to zoom
      const currentDistance = getTouchDistance(touchList);
      const currentCenter = getTouchCenter(touchList);
      
      if (lastTouchDistance > 0) {
        const scaleChange = currentDistance / lastTouchDistance;
        const newScale = Math.max(minZoom, Math.min(maxZoom, scale * scaleChange));
        
        // Zoom towards the center of the pinch
        const centerDelta = {
          x: currentCenter.x - lastTouchCenter.x,
          y: currentCenter.y - lastTouchCenter.y
        };
        
        const newPosition = {
          x: position.x + centerDelta.x,
          y: position.y + centerDelta.y
        };
        
        setScale(newScale);
        setPosition(constrainPosition(newPosition, newScale));
        setLastTouchCenter(currentCenter);
      }
      
      setLastTouchDistance(currentDistance);
    } else if (touchList.length === 1 && isDragging && scale > 1) {
      // Pan
      const newPosition = {
        x: touchList[0].clientX - dragStart.x,
        y: touchList[0].clientY - dragStart.y
      };
      setPosition(constrainPosition(newPosition, scale));
    }
  }, [touches, lastTouchDistance, lastTouchCenter, scale, position, isDragging, dragStart, minZoom, maxZoom, getTouchDistance, getTouchCenter, constrainPosition]);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    setTouches(null);
    setLastTouchDistance(0);
  }, []);

  // Handle hotspot click
  const handleHotspotClick = useCallback((hotspot: Hotspot, e: React.MouseEvent | React.TouchEvent) => {
    e.stopPropagation();
    
    if (mode === 'study') {
      const newClickedHotspots = new Set(clickedHotspots);
      
      if (clickedHotspots.has(hotspot.id)) {
        newClickedHotspots.delete(hotspot.id);
      } else {
        newClickedHotspots.add(hotspot.id);
      }
      
      setClickedHotspots(newClickedHotspots);
      onHotspotClick?.(hotspot);
      
      // Determine validation state
      const clickedCorrectCount = Array.from(newClickedHotspots)
        .filter(id => hotspots.find(h => h.id === id)?.correct).length;
      const clickedIncorrectCount = Array.from(newClickedHotspots)
        .filter(id => !hotspots.find(h => h.id === id)?.correct).length;
      
      // Check if all correct hotspots are clicked
      if (clickedCorrectCount === correctHotspots.length) {
        setShowFeedback(true);
        
        if (clickedIncorrectCount === 0) {
          setFeedbackType('success');
        } else {
          setFeedbackType('partial');
        }
        
        setTimeout(() => {
          const allCorrect = clickedIncorrectCount === 0;
          onValidationComplete?.(allCorrect, Array.from(newClickedHotspots)
            .map(id => hotspots.find(h => h.id === id))
            .filter(Boolean) as Hotspot[]);
        }, 1500);
      } else if (clickedIncorrectCount > 0 && clickedCorrectCount < correctHotspots.length) {
        // Show partial feedback for mixed results
        setShowFeedback(true);
        setFeedbackType('error');
        
        setTimeout(() => {
          setShowFeedback(false);
        }, 2000);
      }
    }
  }, [mode, clickedHotspots, hotspots, correctHotspots, onHotspotClick, onValidationComplete]);

  // Keyboard controls
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!enableKeyboardControls) return;
    
    switch (e.key) {
      case '+':
      case '=':
        e.preventDefault();
        handleZoomIn();
        break;
      case '-':
        e.preventDefault();
        handleZoomOut();
        break;
      case '0':
        e.preventDefault();
        handleResetView();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        if (scale > 1) {
          setPosition(prev => constrainPosition({ x: prev.x + 20, y: prev.y }, scale));
        }
        break;
      case 'ArrowRight':
        e.preventDefault();
        if (scale > 1) {
          setPosition(prev => constrainPosition({ x: prev.x - 20, y: prev.y }, scale));
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (scale > 1) {
          setPosition(prev => constrainPosition({ x: prev.x, y: prev.y + 20 }, scale));
        }
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (scale > 1) {
          setPosition(prev => constrainPosition({ x: prev.x, y: prev.y - 20 }, scale));
        }
        break;
    }
  }, [enableKeyboardControls, handleZoomIn, handleZoomOut, handleResetView, scale, constrainPosition]);

  // Event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false });
      return () => container.removeEventListener('wheel', handleWheel);
    }
  }, [handleWheel]);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  useEffect(() => {
    if (enableKeyboardControls) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [enableKeyboardControls, handleKeyDown]);

  return (
    <div 
      className={`relative bg-gray-100 rounded-lg overflow-hidden ${className}`}
      role="application"
      aria-label="Interactive image with hotspots"
    >
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col space-y-2">
        <div className="bg-white/90 backdrop-blur-sm rounded-lg p-1 shadow-lg">
          <button
            onClick={handleZoomIn}
            disabled={scale >= maxZoom}
            className="p-2 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Zoom in (+)"
            aria-label="Zoom in"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
          
          <button
            onClick={handleZoomOut}
            disabled={scale <= minZoom}
            className="p-2 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Zoom out (-)"
            aria-label="Zoom out"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10h-3" />
            </svg>
          </button>
          
          <button
            onClick={handleResetView}
            disabled={scale === 1 && position.x === 0 && position.y === 0}
            className="p-2 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Reset view (0)"
            aria-label="Reset view"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        
        {/* Zoom indicator */}
        <div className="bg-white/90 backdrop-blur-sm rounded-lg px-3 py-1 shadow-lg text-xs font-medium text-gray-700">
          {Math.round(scale * 100)}%
        </div>
      </div>

      {/* Image container */}
      <div
        ref={containerRef}
        className={`relative w-full h-96 overflow-hidden select-none ${
          scale > 1 ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'
        }`}
        onMouseDown={handleMouseDown}
        onDoubleClick={handleDoubleClick}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        tabIndex={0}
        role="img"
        aria-label={`Interactive image with ${hotspots.length} hotspots`}
      >
        {!imageError ? (
          <motion.div
            className="relative w-full h-full flex items-center justify-center"
            animate={{
              x: position.x,
              y: position.y,
              scale: scale
            }}
            transition={{
              type: "tween",
              duration: isTransitioning ? 0.2 : 0,
              ease: "easeOut"
            }}
            drag={scale > 1}
            dragConstraints={containerRef}
            dragElastic={0.1}
            onDragEnd={(_, info: PanInfo) => {
              if (scale > 1) {
                const newPosition = {
                  x: position.x + info.offset.x,
                  y: position.y + info.offset.y
                };
                setPosition(constrainPosition(newPosition, scale));
              }
            }}
          >
            <img
              ref={imageRef}
              src={imageSrc}
              alt="Interactive image with clickable hotspots"
              className="max-w-full max-h-full object-contain pointer-events-none"
              onLoad={handleImageLoad}
              onError={() => setImageError(true)}
              draggable={false}
            />
            
            {/* Hotspots */}
            {imageLoaded && hotspots.map((hotspot, index) => {
              const isClicked = clickedHotspots.has(hotspot.id);
              const isHovered = hoveredHotspot === hotspot.id;
              const shouldShow = mode === 'answer' || isClicked || isHovered;
              
              return (
                <div
                  key={hotspot.id}
                  className="absolute pointer-events-auto"
                  style={{
                    left: `${hotspot.x}%`,
                    top: `${hotspot.y}%`,
                    width: `${hotspot.width}%`,
                    height: `${hotspot.height}%`,
                    transform: 'translate(-50%, -50%)'
                  }}
                >
                  {/* Hotspot button */}
                  <button
                    className={`
                      w-full h-full rounded-lg border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                      ${mode === 'study' 
                        ? (isClicked 
                          ? (hotspot.correct ? 'border-green-500 bg-green-500/30 shadow-lg' : 'border-red-500 bg-red-500/30 shadow-lg')
                          : 'border-blue-500 bg-blue-500/10 hover:bg-blue-500/20 hover:border-blue-600 cursor-pointer'
                        )
                        : (hotspot.correct 
                          ? 'border-green-500 bg-green-500/30 shadow-lg' 
                          : 'border-red-500 bg-red-500/20 shadow-lg'
                        )
                      }
                    `}
                    onClick={(e) => handleHotspotClick(hotspot, e)}
                    onMouseEnter={() => setHoveredHotspot(hotspot.id)}
                    onMouseLeave={() => setHoveredHotspot(null)}
                    onTouchStart={(e) => {
                      setHoveredHotspot(hotspot.id);
                      // Prevent touch from triggering pan
                      e.stopPropagation();
                    }}
                    onTouchEnd={(e) => {
                      handleHotspotClick(hotspot, e);
                      setTimeout(() => setHoveredHotspot(null), 1000);
                    }}
                    disabled={mode === 'answer'}
                    aria-label={`Hotspot ${index + 1}: ${hotspot.label}`}
                    aria-pressed={isClicked}
                    title={hotspot.description || hotspot.label}
                  >
                    {/* Pulse animation for correct hotspots in answer mode */}
                    {mode === 'answer' && hotspot.correct && (
                      <motion.div
                        className="absolute inset-0 rounded-lg border-2 border-green-400"
                        animate={{
                          scale: [1, 1.1, 1],
                          opacity: [0.5, 0.8, 0.5]
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      />
                    )}
                  </button>
                  
                  {/* Hotspot label */}
                  <AnimatePresence>
                    {shouldShow && (
                      <motion.div
                        className="absolute -top-2 left-1/2 transform -translate-x-1/2 -translate-y-full pointer-events-none z-10"
                        initial={{ opacity: 0, y: 10, scale: 0.8 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.8 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="bg-gray-900/90 backdrop-blur-sm text-white text-xs px-3 py-2 rounded-lg shadow-lg max-w-xs">
                          <div className="font-medium">{hotspot.label}</div>
                          {hotspot.description && (
                            <div className="text-gray-300 mt-1 text-xs">
                              {hotspot.description}
                            </div>
                          )}
                          {/* Arrow pointing down */}
                          <div className="absolute top-full left-1/2 transform -translate-x-1/2">
                            <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900/90"></div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </motion.div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z" />
            </svg>
            <p className="text-lg font-medium">Image not available</p>
          </div>
        )}
      </div>

      {/* Feedback overlay */}
      <AnimatePresence>
        {showFeedback && (
          <motion.div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-white rounded-xl p-6 max-w-sm mx-4 shadow-2xl"
              initial={{ scale: 0.8, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
            >
              <div className="text-center">
                <div className={`mx-auto flex items-center justify-center h-16 w-16 rounded-full mb-4 ${
                  feedbackType === 'success' ? 'bg-green-100' :
                  feedbackType === 'partial' ? 'bg-yellow-100' : 'bg-red-100'
                }`}>
                  {feedbackType === 'success' && (
                    <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {feedbackType === 'partial' && (
                    <svg className="h-8 w-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  )}
                  {feedbackType === 'error' && (
                    <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                </div>
                
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feedbackType === 'success' && 'Perfect!'}
                  {feedbackType === 'partial' && 'Almost there!'}
                  {feedbackType === 'error' && 'Try again'}
                </h3>
                
                <p className="text-sm text-gray-600">
                  {feedbackType === 'success' && 'You identified all the correct areas without any mistakes.'}
                  {feedbackType === 'partial' && 'You found all the key areas, but also selected some incorrect ones.'}
                  {feedbackType === 'error' && 'Some of your selections are incorrect. Keep trying!'}
                </p>
                
                {/* Progress indicator */}
                <div className="mt-4 flex justify-center space-x-1">
                  {Array.from({ length: correctHotspots.length }).map((_, i) => {
                    const correctHotspot = correctHotspots[i];
                    const isFound = clickedHotspots.has(correctHotspot.id);
                    return (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full ${
                          isFound ? 'bg-green-500' : 'bg-gray-300'
                        }`}
                      />
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Instructions */}
      {mode === 'study' && !showFeedback && (
        <motion.div 
          className="absolute bottom-4 left-4 right-4 z-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="bg-white/95 backdrop-blur-sm rounded-xl p-4 shadow-lg border border-gray-200">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-blue-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 mb-2">
                  Find {correctHotspots.length} important {correctHotspots.length === 1 ? 'area' : 'areas'} in this image
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-gray-600">
                  <div className="flex items-center space-x-2">
                    <span>🖱️</span>
                    <span>Click to select areas</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>🔍</span>
                    <span>Scroll/pinch to zoom</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>✋</span>
                    <span>Drag to pan when zoomed</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>⌨️</span>
                    <span>Use +/- keys to zoom</span>
                  </div>
                </div>
                
                {/* Progress */}
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    Progress: {Array.from(clickedHotspots).filter(id => 
                      hotspots.find(h => h.id === id)?.correct
                    ).length} / {correctHotspots.length}
                  </span>
                  <div className="flex space-x-1">
                    {Array.from({ length: correctHotspots.length }).map((_, i) => (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full ${
                          i < Array.from(clickedHotspots).filter(id => 
                            hotspots.find(h => h.id === id)?.correct
                          ).length ? 'bg-blue-500' : 'bg-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Answer mode info */}
      {mode === 'answer' && (
        <motion.div 
          className="absolute bottom-4 left-4 right-4 z-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="bg-green-50/95 backdrop-blur-sm rounded-xl p-4 shadow-lg border border-green-200">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">
                  Answer revealed
                </p>
                <p className="text-xs text-green-700 mt-1">
                  The highlighted areas show the correct answers. Green areas were the targets to find.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}