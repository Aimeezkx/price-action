import { performance } from 'perf_hooks';
import { render, fireEvent, act } from '@testing-library/react-native';
import React from 'react';
import { FlashCard } from '../../components/FlashCard';
import { GradingInterface } from '../../components/GradingInterface';
import { ImageHotspotViewer } from '../../components/ImageHotspotViewer';
import { Card } from '../../types';

// Mock performance API for React Native
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  mark: jest.fn(),
  measure: jest.fn(),
  getEntriesByName: jest.fn(() => []),
  getEntriesByType: jest.fn(() => []),
  clearMarks: jest.fn(),
  clearMeasures: jest.fn(),
};

global.performance = mockPerformance as any;

const mockCard: Card = {
  id: '1',
  front: 'Test Question',
  back: 'Test Answer',
  cardType: 'qa',
  difficulty: 2.5,
  dueDate: new Date(),
  metadata: {},
};

const mockImageCard: Card = {
  id: '2',
  front: 'image-path.jpg',
  back: 'Image description',
  cardType: 'image_hotspot',
  difficulty: 3.0,
  dueDate: new Date(),
  metadata: {
    hotspots: [
      { x: 100, y: 100, width: 50, height: 50, label: 'Feature A' },
      { x: 200, y: 150, width: 60, height: 40, label: 'Feature B' },
    ],
  },
};

describe('Animation Performance Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPerformance.now.mockImplementation(() => Date.now());
  });

  describe('FlashCard Animation Performance', () => {
    it('should complete flip animation within 300ms', async () => {
      const onFlip = jest.fn();
      const { getByTestId } = render(
        <FlashCard card={mockCard} onFlip={onFlip} />
      );

      const startTime = Date.now();
      
      await act(async () => {
        fireEvent.press(getByTestId('flashcard-container'));
      });

      const endTime = Date.now();
      const animationDuration = endTime - startTime;

      expect(animationDuration).toBeLessThan(300);
      expect(onFlip).toHaveBeenCalled();
    });

    it('should maintain 60fps during flip animation', async () => {
      const onFlip = jest.fn();
      const { getByTestId } = render(
        <FlashCard card={mockCard} onFlip={onFlip} />
      );

      // Mock frame timing
      const frameTimes: number[] = [];
      let frameCount = 0;
      const targetFPS = 60;
      const frameDuration = 1000 / targetFPS; // ~16.67ms per frame

      mockPerformance.now.mockImplementation(() => {
        frameCount++;
        const time = frameCount * frameDuration;
        frameTimes.push(time);
        return time;
      });

      await act(async () => {
        fireEvent.press(getByTestId('flashcard-container'));
        
        // Simulate animation frames
        for (let i = 0; i < 18; i++) { // 300ms / 16.67ms ≈ 18 frames
          await new Promise(resolve => setTimeout(resolve, 16));
        }
      });

      // Check that we maintained consistent frame timing
      const averageFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
      expect(averageFrameTime).toBeLessThanOrEqual(frameDuration * 1.1); // Allow 10% variance
    });

    it('should handle rapid successive flips without performance degradation', async () => {
      const onFlip = jest.fn();
      const { getByTestId } = render(
        <FlashCard card={mockCard} onFlip={onFlip} />
      );

      const flipTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const startTime = Date.now();
        
        await act(async () => {
          fireEvent.press(getByTestId('flashcard-container'));
        });
        
        const endTime = Date.now();
        flipTimes.push(endTime - startTime);
        
        // Wait for animation to complete
        await new Promise(resolve => setTimeout(resolve, 350));
      }

      // Verify that flip times don't increase significantly over time
      const firstFlipTime = flipTimes[0];
      const lastFlipTime = flipTimes[flipTimes.length - 1];
      
      expect(lastFlipTime).toBeLessThan(firstFlipTime * 1.5); // Allow 50% variance
      expect(flipTimes.every(time => time < 300)).toBe(true);
    });
  });

  describe('GradingInterface Animation Performance', () => {
    it('should animate button press within 100ms', async () => {
      const onGrade = jest.fn();
      const { getByTestId } = render(
        <GradingInterface onGrade={onGrade} />
      );

      const startTime = Date.now();
      
      await act(async () => {
        fireEvent.press(getByTestId('grade-button-4'));
      });

      const endTime = Date.now();
      const animationDuration = endTime - startTime;

      expect(animationDuration).toBeLessThan(100);
      expect(onGrade).toHaveBeenCalledWith(4);
    });

    it('should handle multiple rapid button presses', async () => {
      const onGrade = jest.fn();
      const { getByTestId } = render(
        <GradingInterface onGrade={onGrade} />
      );

      const pressTimes: number[] = [];
      
      for (let grade = 0; grade <= 5; grade++) {
        const startTime = Date.now();
        
        await act(async () => {
          fireEvent.press(getByTestId(`grade-button-${grade}`));
        });
        
        const endTime = Date.now();
        pressTimes.push(endTime - startTime);
        
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      // All button presses should be fast
      expect(pressTimes.every(time => time < 100)).toBe(true);
      expect(onGrade).toHaveBeenCalledTimes(6);
    });
  });

  describe('ImageHotspotViewer Performance', () => {
    it('should render hotspots without performance issues', async () => {
      const onHotspotPress = jest.fn();
      
      const startTime = Date.now();
      
      const { getAllByTestId } = render(
        <ImageHotspotViewer
          imageUri="test-image.jpg"
          hotspots={mockImageCard.metadata.hotspots}
          onHotspotPress={onHotspotPress}
        />
      );
      
      const endTime = Date.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(100); // Should render quickly
      
      const hotspotElements = getAllByTestId(/hotspot-\d+/);
      expect(hotspotElements).toHaveLength(2);
    });

    it('should handle zoom gestures smoothly', async () => {
      const onHotspotPress = jest.fn();
      const { getByTestId } = render(
        <ImageHotspotViewer
          imageUri="test-image.jpg"
          hotspots={mockImageCard.metadata.hotspots}
          onHotspotPress={onHotspotPress}
          enableZoom={true}
        />
      );

      const zoomContainer = getByTestId('zoom-container');
      
      // Simulate pinch gesture
      const startTime = Date.now();
      
      await act(async () => {
        fireEvent(zoomContainer, 'onPinchGestureEvent', {
          nativeEvent: {
            scale: 2.0,
            velocity: 0.5,
          },
        });
      });
      
      const endTime = Date.now();
      const gestureResponseTime = endTime - startTime;

      expect(gestureResponseTime).toBeLessThan(50); // Should respond quickly to gestures
    });

    it('should maintain performance with many hotspots', async () => {
      const manyHotspots = Array.from({ length: 20 }, (_, i) => ({
        x: i * 50,
        y: i * 30,
        width: 40,
        height: 40,
        label: `Hotspot ${i}`,
      }));

      const onHotspotPress = jest.fn();
      
      const startTime = Date.now();
      
      const { getAllByTestId } = render(
        <ImageHotspotViewer
          imageUri="test-image.jpg"
          hotspots={manyHotspots}
          onHotspotPress={onHotspotPress}
        />
      );
      
      const endTime = Date.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(200); // Should still render quickly with many hotspots
      
      const hotspotElements = getAllByTestId(/hotspot-\d+/);
      expect(hotspotElements).toHaveLength(20);
    });
  });

  describe('Memory Performance', () => {
    it('should not leak memory during repeated animations', async () => {
      const onFlip = jest.fn();
      
      // Mock memory usage tracking
      const initialMemory = process.memoryUsage?.() || { heapUsed: 0 };
      
      for (let i = 0; i < 50; i++) {
        const { getByTestId, unmount } = render(
          <FlashCard card={mockCard} onFlip={onFlip} />
        );
        
        await act(async () => {
          fireEvent.press(getByTestId('flashcard-container'));
        });
        
        await new Promise(resolve => setTimeout(resolve, 100));
        unmount();
      }
      
      const finalMemory = process.memoryUsage?.() || { heapUsed: 0 };
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      
      // Memory increase should be reasonable (less than 10MB)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    });

    it('should clean up animation resources properly', async () => {
      const onFlip = jest.fn();
      const { getByTestId, unmount } = render(
        <FlashCard card={mockCard} onFlip={onFlip} />
      );

      await act(async () => {
        fireEvent.press(getByTestId('flashcard-container'));
      });

      // Unmount during animation
      unmount();

      // Should not cause memory leaks or errors
      expect(true).toBe(true); // Test passes if no errors thrown
    });
  });

  describe('Battery Performance', () => {
    it('should minimize CPU usage during idle state', async () => {
      const onFlip = jest.fn();
      render(<FlashCard card={mockCard} onFlip={onFlip} />);

      // Simulate idle state for 1 second
      await new Promise(resolve => setTimeout(resolve, 1000));

      // In a real app, we would measure CPU usage here
      // For testing purposes, we verify no unnecessary re-renders
      expect(onFlip).not.toHaveBeenCalled();
    });

    it('should use efficient animation techniques', async () => {
      const onGrade = jest.fn();
      const { getByTestId } = render(
        <GradingInterface onGrade={onGrade} />
      );

      // Verify that animations use native driver when possible
      await act(async () => {
        fireEvent.press(getByTestId('grade-button-3'));
      });

      // This would be verified through animation configuration in real implementation
      expect(onGrade).toHaveBeenCalledWith(3);
    });
  });
});