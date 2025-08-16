/**
 * Frontend loading time measurements and performance tests.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { performance } from 'perf_hooks';

import App from '../../App';
import { DocumentsPage } from '../../pages/DocumentsPage';
import { SearchPage } from '../../pages/SearchPage';
import { StudyPage } from '../../pages/StudyPage';
import { DocumentUpload } from '../../components/DocumentUpload';
import { FlashCard } from '../../components/FlashCard';
import { SearchResults } from '../../components/SearchResults';

interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  interactionTime: number;
  memoryUsage?: number;
}

interface PerformanceThresholds {
  maxLoadTime: number;
  maxRenderTime: number;
  maxInteractionTime: number;
  maxMemoryUsage?: number;
}

class FrontendPerformanceMonitor {
  private startTime: number = 0;
  private endTime: number = 0;
  private renderStartTime: number = 0;
  private renderEndTime: number = 0;

  startTiming(): void {
    this.startTime = performance.now();
  }

  endTiming(): void {
    this.endTime = performance.now();
  }

  startRenderTiming(): void {
    this.renderStartTime = performance.now();
  }

  endRenderTiming(): void {
    this.renderEndTime = performance.now();
  }

  getLoadTime(): number {
    return this.endTime - this.startTime;
  }

  getRenderTime(): number {
    return this.renderEndTime - this.renderStartTime;
  }

  getMemoryUsage(): number {
    // @ts-ignore - performance.memory is available in Chrome
    if (typeof performance.memory !== 'undefined') {
      // @ts-ignore
      return performance.memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    return 0;
  }

  async measureInteractionTime(interaction: () => Promise<void>): Promise<number> {
    const startTime = performance.now();
    await interaction();
    const endTime = performance.now();
    return endTime - startTime;
  }
}

const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
    },
  });
};

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Frontend Performance Tests', () => {
  let performanceMonitor: FrontendPerformanceMonitor;
  let queryClient: QueryClient;

  const performanceThresholds: PerformanceThresholds = {
    maxLoadTime: 2000, // 2 seconds
    maxRenderTime: 500, // 500ms
    maxInteractionTime: 200, // 200ms
    maxMemoryUsage: 200, // 200MB
  };

  beforeEach(() => {
    performanceMonitor = new FrontendPerformanceMonitor();
    queryClient = createTestQueryClient();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('Application Loading Performance', () => {
    it('should load main application within performance threshold', async () => {
      performanceMonitor.startTiming();
      performanceMonitor.startRenderTiming();

      const { container } = render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );

      // Wait for initial render to complete
      await waitFor(() => {
        expect(container.firstChild).toBeTruthy();
      });

      performanceMonitor.endRenderTiming();
      performanceMonitor.endTiming();

      const loadTime = performanceMonitor.getLoadTime();
      const renderTime = performanceMonitor.getRenderTime();
      const memoryUsage = performanceMonitor.getMemoryUsage();

      console.log(`\nApp Loading Performance:`);
      console.log(`  Load time: ${loadTime.toFixed(2)}ms`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);
      console.log(`  Memory usage: ${memoryUsage.toFixed(2)}MB`);

      expect(loadTime).toBeLessThan(performanceThresholds.maxLoadTime);
      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime);
      
      if (memoryUsage > 0) {
        expect(memoryUsage).toBeLessThan(performanceThresholds.maxMemoryUsage!);
      }
    });

    it('should load documents page efficiently', async () => {
      performanceMonitor.startTiming();
      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <DocumentsPage />
        </TestWrapper>
      );

      // Wait for page to render
      await waitFor(() => {
        expect(screen.getByText(/documents/i)).toBeInTheDocument();
      });

      performanceMonitor.endRenderTiming();
      performanceMonitor.endTiming();

      const loadTime = performanceMonitor.getLoadTime();
      const renderTime = performanceMonitor.getRenderTime();

      console.log(`\nDocuments Page Performance:`);
      console.log(`  Load time: ${loadTime.toFixed(2)}ms`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);

      expect(loadTime).toBeLessThan(performanceThresholds.maxLoadTime);
      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime);
    });

    it('should load search page efficiently', async () => {
      performanceMonitor.startTiming();
      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <SearchPage />
        </TestWrapper>
      );

      // Wait for search interface to render
      await waitFor(() => {
        expect(screen.getByRole('textbox')).toBeInTheDocument();
      });

      performanceMonitor.endRenderTiming();
      performanceMonitor.endTiming();

      const loadTime = performanceMonitor.getLoadTime();
      const renderTime = performanceMonitor.getRenderTime();

      console.log(`\nSearch Page Performance:`);
      console.log(`  Load time: ${loadTime.toFixed(2)}ms`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);

      expect(loadTime).toBeLessThan(performanceThresholds.maxLoadTime);
      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime);
    });

    it('should load study page efficiently', async () => {
      performanceMonitor.startTiming();
      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <StudyPage />
        </TestWrapper>
      );

      // Wait for study interface to render
      await waitFor(() => {
        expect(screen.getByText(/study/i)).toBeInTheDocument();
      });

      performanceMonitor.endRenderTiming();
      performanceMonitor.endTiming();

      const loadTime = performanceMonitor.getLoadTime();
      const renderTime = performanceMonitor.getRenderTime();

      console.log(`\nStudy Page Performance:`);
      console.log(`  Load time: ${loadTime.toFixed(2)}ms`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);

      expect(loadTime).toBeLessThan(performanceThresholds.maxLoadTime);
      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime);
    });
  });

  describe('Component Rendering Performance', () => {
    it('should render document upload component efficiently', async () => {
      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <DocumentUpload onUpload={() => {}} />
        </TestWrapper>
      );

      performanceMonitor.endRenderTiming();

      const renderTime = performanceMonitor.getRenderTime();

      console.log(`\nDocument Upload Component Performance:`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);

      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime);
    });

    it('should render flashcard component efficiently', async () => {
      const mockCard = {
        id: '1',
        question: 'What is machine learning?',
        answer: 'A subset of artificial intelligence',
        difficulty: 0.5,
        due_date: new Date().toISOString(),
        interval: 1,
        ease_factor: 2.5,
        repetitions: 0
      };

      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <FlashCard
            card={mockCard}
            onGrade={() => {}}
            showAnswer={false}
            onFlip={() => {}}
          />
        </TestWrapper>
      );

      performanceMonitor.endRenderTiming();

      const renderTime = performanceMonitor.getRenderTime();

      console.log(`\nFlashCard Component Performance:`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);

      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime);
    });

    it('should render search results efficiently with multiple items', async () => {
      const mockResults = Array.from({ length: 20 }, (_, i) => ({
        id: `result-${i}`,
        title: `Search Result ${i + 1}`,
        content: `This is the content for search result ${i + 1}`,
        score: 0.9 - (i * 0.01),
        document_id: `doc-${i}`,
        chapter_id: `chapter-${i}`
      }));

      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <SearchResults
            results={mockResults}
            isLoading={false}
            onResultClick={() => {}}
          />
        </TestWrapper>
      );

      performanceMonitor.endRenderTiming();

      const renderTime = performanceMonitor.getRenderTime();

      console.log(`\nSearch Results Component Performance (20 items):`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);

      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime * 2); // Allow more time for multiple items
    });
  });

  describe('User Interaction Performance', () => {
    it('should handle search input interactions efficiently', async () => {
      const { getByRole } = render(
        <TestWrapper>
          <SearchPage />
        </TestWrapper>
      );

      const searchInput = getByRole('textbox');

      const interactionTime = await performanceMonitor.measureInteractionTime(async () => {
        // Simulate typing in search input
        searchInput.focus();
        
        // Simulate typing multiple characters
        for (let i = 0; i < 10; i++) {
          const event = new Event('input', { bubbles: true });
          Object.defineProperty(event, 'target', {
            value: { value: 'test query'.slice(0, i + 1) },
            enumerable: true
          });
          searchInput.dispatchEvent(event);
          
          // Small delay to simulate real typing
          await new Promise(resolve => setTimeout(resolve, 10));
        }
      });

      console.log(`\nSearch Input Interaction Performance:`);
      console.log(`  Interaction time: ${interactionTime.toFixed(2)}ms`);

      expect(interactionTime).toBeLessThan(performanceThresholds.maxInteractionTime * 2); // Allow more time for multiple inputs
    });

    it('should handle flashcard flip interactions efficiently', async () => {
      const mockCard = {
        id: '1',
        question: 'What is machine learning?',
        answer: 'A subset of artificial intelligence',
        difficulty: 0.5,
        due_date: new Date().toISOString(),
        interval: 1,
        ease_factor: 2.5,
        repetitions: 0
      };

      let showAnswer = false;
      const handleFlip = () => {
        showAnswer = !showAnswer;
      };

      const { rerender } = render(
        <TestWrapper>
          <FlashCard
            card={mockCard}
            onGrade={() => {}}
            showAnswer={showAnswer}
            onFlip={handleFlip}
          />
        </TestWrapper>
      );

      const interactionTime = await performanceMonitor.measureInteractionTime(async () => {
        // Simulate multiple card flips
        for (let i = 0; i < 5; i++) {
          handleFlip();
          rerender(
            <TestWrapper>
              <FlashCard
                card={mockCard}
                onGrade={() => {}}
                showAnswer={showAnswer}
                onFlip={handleFlip}
              />
            </TestWrapper>
          );
          
          // Small delay to simulate real interaction
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      });

      console.log(`\nFlashCard Flip Interaction Performance:`);
      console.log(`  Interaction time: ${interactionTime.toFixed(2)}ms`);

      expect(interactionTime).toBeLessThan(performanceThresholds.maxInteractionTime * 5); // Allow time for multiple flips
    });
  });

  describe('Memory Usage Performance', () => {
    it('should maintain reasonable memory usage during component lifecycle', async () => {
      const initialMemory = performanceMonitor.getMemoryUsage();

      // Render and unmount components multiple times
      for (let i = 0; i < 10; i++) {
        const { unmount } = render(
          <TestWrapper>
            <DocumentsPage />
          </TestWrapper>
        );
        
        unmount();
        
        // Force garbage collection if available
        if (global.gc) {
          global.gc();
        }
      }

      const finalMemory = performanceMonitor.getMemoryUsage();
      const memoryGrowth = finalMemory - initialMemory;

      console.log(`\nMemory Usage Performance:`);
      console.log(`  Initial memory: ${initialMemory.toFixed(2)}MB`);
      console.log(`  Final memory: ${finalMemory.toFixed(2)}MB`);
      console.log(`  Memory growth: ${memoryGrowth.toFixed(2)}MB`);

      // Memory growth should be minimal (less than 50MB for 10 cycles)
      if (initialMemory > 0 && finalMemory > 0) {
        expect(memoryGrowth).toBeLessThan(50);
      }
    });

    it('should handle large datasets efficiently', async () => {
      const initialMemory = performanceMonitor.getMemoryUsage();

      // Create large mock dataset
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: `item-${i}`,
        title: `Large Dataset Item ${i + 1}`,
        content: `This is content for item ${i + 1}`.repeat(10),
        score: Math.random(),
        document_id: `doc-${i}`,
        chapter_id: `chapter-${i % 10}`
      }));

      performanceMonitor.startRenderTiming();

      render(
        <TestWrapper>
          <SearchResults
            results={largeDataset}
            isLoading={false}
            onResultClick={() => {}}
          />
        </TestWrapper>
      );

      performanceMonitor.endRenderTiming();

      const finalMemory = performanceMonitor.getMemoryUsage();
      const renderTime = performanceMonitor.getRenderTime();
      const memoryUsage = finalMemory - initialMemory;

      console.log(`\nLarge Dataset Performance:`);
      console.log(`  Dataset size: ${largeDataset.length} items`);
      console.log(`  Render time: ${renderTime.toFixed(2)}ms`);
      console.log(`  Memory usage: ${memoryUsage.toFixed(2)}MB`);

      expect(renderTime).toBeLessThan(performanceThresholds.maxRenderTime * 10); // Allow more time for large dataset
      
      if (memoryUsage > 0) {
        expect(memoryUsage).toBeLessThan(performanceThresholds.maxMemoryUsage! * 2); // Allow more memory for large dataset
      }
    });
  });

  describe('Concurrent Operations Performance', () => {
    it('should handle multiple simultaneous component renders efficiently', async () => {
      const components = [
        () => <DocumentsPage />,
        () => <SearchPage />,
        () => <StudyPage />,
      ];

      performanceMonitor.startTiming();

      // Render multiple components simultaneously
      const renders = components.map(Component => 
        render(
          <TestWrapper>
            <Component />
          </TestWrapper>
        )
      );

      // Wait for all components to be rendered
      await Promise.all(
        renders.map(({ container }) => 
          waitFor(() => expect(container.firstChild).toBeTruthy())
        )
      );

      performanceMonitor.endTiming();

      const totalTime = performanceMonitor.getLoadTime();
      const memoryUsage = performanceMonitor.getMemoryUsage();

      console.log(`\nConcurrent Rendering Performance:`);
      console.log(`  Components rendered: ${components.length}`);
      console.log(`  Total time: ${totalTime.toFixed(2)}ms`);
      console.log(`  Memory usage: ${memoryUsage.toFixed(2)}MB`);

      expect(totalTime).toBeLessThan(performanceThresholds.maxLoadTime * 2); // Allow more time for multiple components
      
      if (memoryUsage > 0) {
        expect(memoryUsage).toBeLessThan(performanceThresholds.maxMemoryUsage! * 1.5);
      }

      // Cleanup
      renders.forEach(({ unmount }) => unmount());
    });
  });
});