import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View,
  Image,
  TouchableOpacity,
  Animated,
  Dimensions,
  StyleSheet,
  Text,
  PanResponder,
} from 'react-native';
import {
  PanGestureHandler,
  PinchGestureHandler,
  State,
} from 'react-native-gesture-handler';
import { hapticService } from '../services/hapticService';
import type { Hotspot } from '../types';

interface ImageHotspotViewerProps {
  imageSrc: string;
  hotspots: Hotspot[];
  mode: 'study' | 'answer';
  onHotspotClick?: (hotspot: Hotspot) => void;
  onValidationComplete?: (correct: boolean, clickedHotspots: Hotspot[]) => void;
  maxZoom?: number;
  minZoom?: number;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export function ImageHotspotViewer({
  imageSrc,
  hotspots,
  mode,
  onHotspotClick,
  onValidationComplete,
  maxZoom = 4,
  minZoom = 0.5,
}: ImageHotspotViewerProps) {
  // Animation values
  const scale = useRef(new Animated.Value(1)).current;
  const translateX = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(0)).current;
  const pinchScale = useRef(new Animated.Value(1)).current;
  const panX = useRef(new Animated.Value(0)).current;
  const panY = useRef(new Animated.Value(0)).current;

  // State
  const [clickedHotspots, setClickedHotspots] = useState<Set<string>>(new Set());
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'success' | 'partial' | 'error'>('success');

  // Refs for gesture handling
  const baseScale = useRef(1);
  const baseTranslateX = useRef(0);
  const baseTranslateY = useRef(0);
  const lastScale = useRef(1);
  const lastTranslateX = useRef(0);
  const lastTranslateY = useRef(0);

  const correctHotspots = hotspots.filter(h => h.correct);

  // Reset state when mode changes
  useEffect(() => {
    if (mode === 'study') {
      setClickedHotspots(new Set());
      setShowFeedback(false);
      setFeedbackType('success');
    }
  }, [mode]);

  // Handle image load
  const handleImageLoad = useCallback((event: any) => {
    const { width, height } = event.nativeEvent.source;
    setImageDimensions({ width, height });
    setImageLoaded(true);
  }, []);

  // Calculate constrained position
  const constrainPosition = useCallback((x: number, y: number, currentScale: number) => {
    const containerWidth = screenWidth;
    const containerHeight = 400; // Fixed height for the viewer
    
    const scaledImageWidth = imageDimensions.width * currentScale;
    const scaledImageHeight = imageDimensions.height * currentScale;
    
    const maxX = Math.max(0, (scaledImageWidth - containerWidth) / 2);
    const maxY = Math.max(0, (scaledImageHeight - containerHeight) / 2);
    
    return {
      x: Math.max(-maxX, Math.min(maxX, x)),
      y: Math.max(-maxY, Math.min(maxY, y)),
    };
  }, [imageDimensions]);

  // Handle pinch gesture
  const onPinchGestureEvent = Animated.event(
    [{ nativeEvent: { scale: pinchScale } }],
    { useNativeDriver: true }
  );

  const onPinchHandlerStateChange = useCallback((event: any) => {
    if (event.nativeEvent.oldState === State.ACTIVE) {
      const newScale = Math.max(minZoom, Math.min(maxZoom, lastScale.current * event.nativeEvent.scale));
      
      baseScale.current = newScale;
      lastScale.current = newScale;
      
      // Reset pinch scale
      pinchScale.setValue(1);
      
      // Update main scale
      scale.setValue(newScale);
      
      // Constrain position if needed
      if (newScale <= 1) {
        translateX.setValue(0);
        translateY.setValue(0);
        baseTranslateX.current = 0;
        baseTranslateY.current = 0;
        lastTranslateX.current = 0;
        lastTranslateY.current = 0;
      }
      
      hapticService.cardFlip();
    }
  }, [minZoom, maxZoom, scale, translateX, translateY]);

  // Handle pan gesture
  const onPanGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: panX, translationY: panY } }],
    { useNativeDriver: true }
  );

  const onPanHandlerStateChange = useCallback((event: any) => {
    if (event.nativeEvent.oldState === State.ACTIVE) {
      const newX = lastTranslateX.current + event.nativeEvent.translationX;
      const newY = lastTranslateY.current + event.nativeEvent.translationY;
      
      const constrained = constrainPosition(newX, newY, lastScale.current);
      
      baseTranslateX.current = constrained.x;
      baseTranslateY.current = constrained.y;
      lastTranslateX.current = constrained.x;
      lastTranslateY.current = constrained.y;
      
      // Reset pan values
      panX.setValue(0);
      panY.setValue(0);
      
      // Update main translate values
      translateX.setValue(constrained.x);
      translateY.setValue(constrained.y);
    }
  }, [constrainPosition]);

  // Handle hotspot click
  const handleHotspotClick = useCallback((hotspot: Hotspot) => {
    if (mode === 'answer') return;
    
    hapticService.buttonPress();
    
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
        hapticService.success();
      } else {
        setFeedbackType('partial');
        hapticService.warning();
      }
      
      setTimeout(() => {
        const allCorrect = clickedIncorrectCount === 0;
        onValidationComplete?.(allCorrect, Array.from(newClickedHotspots)
          .map(id => hotspots.find(h => h.id === id))
          .filter(Boolean) as Hotspot[]);
        setShowFeedback(false);
      }, 2000);
    } else if (clickedIncorrectCount > 0 && clickedCorrectCount < correctHotspots.length) {
      // Show brief error feedback
      hapticService.error();
      setShowFeedback(true);
      setFeedbackType('error');
      
      setTimeout(() => {
        setShowFeedback(false);
      }, 1500);
    }
  }, [mode, clickedHotspots, hotspots, correctHotspots, onHotspotClick, onValidationComplete]);

  // Handle double tap to zoom
  const handleDoublePress = useCallback(() => {
    const newScale = lastScale.current > 1 ? 1 : 2;
    
    Animated.parallel([
      Animated.timing(scale, {
        toValue: newScale,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(translateX, {
        toValue: newScale === 1 ? 0 : lastTranslateX.current,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: newScale === 1 ? 0 : lastTranslateY.current,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
    
    baseScale.current = newScale;
    lastScale.current = newScale;
    
    if (newScale === 1) {
      baseTranslateX.current = 0;
      baseTranslateY.current = 0;
      lastTranslateX.current = 0;
      lastTranslateY.current = 0;
    }
    
    hapticService.cardFlip();
  }, [scale, translateX, translateY]);

  // Reset view
  const resetView = useCallback(() => {
    Animated.parallel([
      Animated.timing(scale, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(translateX, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
    
    baseScale.current = 1;
    lastScale.current = 1;
    baseTranslateX.current = 0;
    baseTranslateY.current = 0;
    lastTranslateX.current = 0;
    lastTranslateY.current = 0;
    
    hapticService.buttonPress();
  }, [scale, translateX, translateY]);

  // Render hotspot
  const renderHotspot = useCallback((hotspot: Hotspot, index: number) => {
    const isClicked = clickedHotspots.has(hotspot.id);
    const shouldShow = mode === 'answer' || isClicked;
    
    return (
      <TouchableOpacity
        key={hotspot.id}
        style={[
          styles.hotspot,
          {
            left: `${hotspot.x}%`,
            top: `${hotspot.y}%`,
            width: `${hotspot.width}%`,
            height: `${hotspot.height}%`,
          },
          mode === 'study' 
            ? (isClicked 
              ? (hotspot.correct ? styles.hotspotCorrect : styles.hotspotIncorrect)
              : styles.hotspotDefault
            )
            : (hotspot.correct 
              ? styles.hotspotCorrect 
              : styles.hotspotIncorrect
            )
        ]}
        onPress={() => handleHotspotClick(hotspot)}
        disabled={mode === 'answer'}
        activeOpacity={0.7}
      >
        {shouldShow && (
          <View style={styles.hotspotLabel}>
            <Text style={styles.hotspotLabelText}>{hotspot.label}</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  }, [mode, clickedHotspots, handleHotspotClick]);

  const combinedScale = Animated.multiply(scale, pinchScale);
  const combinedTranslateX = Animated.add(translateX, panX);
  const combinedTranslateY = Animated.add(translateY, panY);

  return (
    <View style={styles.container}>
      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={resetView}
        >
          <Text style={styles.controlButtonText}>Reset</Text>
        </TouchableOpacity>
        
        <View style={styles.progressContainer}>
          <Text style={styles.progressText}>
            {Array.from(clickedHotspots).filter(id => 
              hotspots.find(h => h.id === id)?.correct
            ).length} / {correctHotspots.length}
          </Text>
        </View>
      </View>

      {/* Image viewer */}
      <View style={styles.imageContainer}>
        <PanGestureHandler
          onGestureEvent={onPanGestureEvent}
          onHandlerStateChange={onPanHandlerStateChange}
          enabled={lastScale.current > 1}
        >
          <Animated.View style={styles.panContainer}>
            <PinchGestureHandler
              onGestureEvent={onPinchGestureEvent}
              onHandlerStateChange={onPinchHandlerStateChange}
            >
              <Animated.View style={styles.pinchContainer}>
                <TouchableOpacity
                  onPress={handleDoublePress}
                  activeOpacity={1}
                  style={styles.imageWrapper}
                >
                  <Animated.View
                    style={[
                      styles.animatedImageContainer,
                      {
                        transform: [
                          { scale: combinedScale },
                          { translateX: combinedTranslateX },
                          { translateY: combinedTranslateY },
                        ],
                      },
                    ]}
                  >
                    <Image
                      source={{ uri: imageSrc }}
                      style={styles.image}
                      resizeMode="contain"
                      onLoad={handleImageLoad}
                    />
                    
                    {/* Hotspots */}
                    {imageLoaded && hotspots.map(renderHotspot)}
                  </Animated.View>
                </TouchableOpacity>
              </Animated.View>
            </PinchGestureHandler>
          </Animated.View>
        </PanGestureHandler>
      </View>

      {/* Instructions */}
      {mode === 'study' && !showFeedback && (
        <View style={styles.instructions}>
          <Text style={styles.instructionsTitle}>
            Find {correctHotspots.length} important {correctHotspots.length === 1 ? 'area' : 'areas'}
          </Text>
          <Text style={styles.instructionsText}>
            • Tap areas to select them{'\n'}
            • Pinch to zoom in/out{'\n'}
            • Drag to pan when zoomed{'\n'}
            • Double tap to reset zoom
          </Text>
        </View>
      )}

      {/* Feedback overlay */}
      {showFeedback && (
        <View style={styles.feedbackOverlay}>
          <View style={styles.feedbackContainer}>
            <View style={[
              styles.feedbackIcon,
              feedbackType === 'success' ? styles.feedbackIconSuccess :
              feedbackType === 'partial' ? styles.feedbackIconPartial : styles.feedbackIconError
            ]}>
              <Text style={styles.feedbackIconText}>
                {feedbackType === 'success' ? '✓' : 
                 feedbackType === 'partial' ? '!' : '✗'}
              </Text>
            </View>
            
            <Text style={styles.feedbackTitle}>
              {feedbackType === 'success' && 'Perfect!'}
              {feedbackType === 'partial' && 'Almost there!'}
              {feedbackType === 'error' && 'Try again'}
            </Text>
            
            <Text style={styles.feedbackMessage}>
              {feedbackType === 'success' && 'You identified all the correct areas!'}
              {feedbackType === 'partial' && 'You found all key areas, but selected some incorrect ones.'}
              {feedbackType === 'error' && 'Some selections are incorrect. Keep trying!'}
            </Text>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  controlButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#3B82F6',
    borderRadius: 8,
  },
  controlButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  progressContainer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
  },
  progressText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  imageContainer: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  panContainer: {
    flex: 1,
  },
  pinchContainer: {
    flex: 1,
  },
  imageWrapper: {
    flex: 1,
  },
  animatedImageContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: screenWidth,
    height: 400,
  },
  hotspot: {
    position: 'absolute',
    borderWidth: 2,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  hotspotDefault: {
    borderColor: '#3B82F6',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
  },
  hotspotCorrect: {
    borderColor: '#10B981',
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
  },
  hotspotIncorrect: {
    borderColor: '#EF4444',
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  hotspotLabel: {
    position: 'absolute',
    top: -30,
    left: '50%',
    transform: [{ translateX: -50 }],
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    minWidth: 60,
  },
  hotspotLabelText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  instructions: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  instructionsText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  feedbackOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  feedbackContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    marginHorizontal: 32,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  feedbackIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  feedbackIconSuccess: {
    backgroundColor: '#D1FAE5',
  },
  feedbackIconPartial: {
    backgroundColor: '#FEF3C7',
  },
  feedbackIconError: {
    backgroundColor: '#FEE2E2',
  },
  feedbackIconText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  feedbackTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  feedbackMessage: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
});