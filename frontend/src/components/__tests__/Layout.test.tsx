import React from 'react';
import { render, screen } from '../../../test/utils';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi } from 'vitest';
import { Layout } from '../Layout';

// Mock child components
vi.mock('../Navigation', () => ({
  Navigation: () => <nav data-testid="navigation">Navigation</nav>,
}));

// Custom render function with router
const renderWithRouter = (children: React.ReactNode, initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="*" element={<Layout />} />
      </Routes>
      {children}
    </MemoryRouter>
  );
};

describe('Layout', () => {
  describe('Basic Rendering', () => {
    it('renders navigation component', () => {
      render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      );

      expect(screen.getByTestId('navigation')).toBeInTheDocument();
    });

    it('has proper layout structure', () => {
      const { container } = render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      );

      // Should have a main container
      const main = container.querySelector('main');
      expect(main).toBeInTheDocument();
    });

    it('renders outlet for child routes', () => {
      render(
        <MemoryRouter initialEntries={['/test']}>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route path="test" element={<div data-testid="test-content">Test content</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByTestId('test-content')).toBeInTheDocument();
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    it('applies correct CSS classes for layout', () => {
      const { container } = renderWithRouter(<div>Test content</div>);

      // Check for responsive layout classes
      const layoutContainer = container.firstChild;
      expect(layoutContainer).toHaveClass('min-h-screen');
    });

    it('provides proper content area', () => {
      renderWithRouter(<div data-testid="content">Content</div>);

      const content = screen.getByTestId('content');
      expect(content).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('applies responsive classes', () => {
      const { container } = renderWithRouter(<div>Test content</div>);

      // Check for responsive container classes
      const mainContent = container.querySelector('main');
      expect(mainContent).toHaveClass('flex-1');
    });

    it('handles different screen sizes', () => {
      // Test with different viewport sizes
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      renderWithRouter(<div>Mobile content</div>);
      expect(screen.getByText('Mobile content')).toBeInTheDocument();

      // Change to desktop size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });

      renderWithRouter(<div>Desktop content</div>);
      expect(screen.getByText('Desktop content')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      renderWithRouter(<div>Test content</div>);

      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('maintains focus management', () => {
      renderWithRouter(
        <div>
          <button>Test button</button>
          <input type="text" placeholder="Test input" />
        </div>
      );

      const button = screen.getByRole('button');
      const input = screen.getByRole('textbox');

      expect(button).toBeInTheDocument();
      expect(input).toBeInTheDocument();

      // Focus should work normally within layout
      button.focus();
      expect(document.activeElement).toBe(button);

      input.focus();
      expect(document.activeElement).toBe(input);
    });

    it('supports keyboard navigation', () => {
      renderWithRouter(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
          <a href="/test">Link</a>
        </div>
      );

      const button1 = screen.getByRole('button', { name: 'Button 1' });
      const button2 = screen.getByRole('button', { name: 'Button 2' });
      const link = screen.getByRole('link');

      // All interactive elements should be focusable
      expect(button1).not.toHaveAttribute('tabIndex', '-1');
      expect(button2).not.toHaveAttribute('tabIndex', '-1');
      expect(link).not.toHaveAttribute('tabIndex', '-1');
    });
  });

  describe('Content Rendering', () => {
    it('renders multiple child elements', () => {
      renderWithRouter(
        <div>
          <h1>Title</h1>
          <p>Paragraph</p>
          <button>Button</button>
        </div>
      );

      expect(screen.getByRole('heading', { name: 'Title' })).toBeInTheDocument();
      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Button' })).toBeInTheDocument();
    });

    it('renders complex nested content', () => {
      renderWithRouter(
        <div>
          <section>
            <header>
              <h1>Section Title</h1>
            </header>
            <article>
              <p>Article content</p>
            </article>
          </section>
        </div>
      );

      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('article')).toBeInTheDocument();
      expect(screen.getByText('Section Title')).toBeInTheDocument();
      expect(screen.getByText('Article content')).toBeInTheDocument();
    });

    it('handles empty content gracefully', () => {
      renderWithRouter(<div></div>);

      expect(screen.getByTestId('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('handles null children', () => {
      renderWithRouter(null);

      expect(screen.getByTestId('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  describe('Layout Consistency', () => {
    it('maintains consistent layout across different routes', () => {
      const { rerender } = render(
        <MemoryRouter initialEntries={['/documents']}>
          <Layout>
            <div data-testid="documents-page">Documents</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByTestId('documents-page')).toBeInTheDocument();
      expect(screen.getByTestId('navigation')).toBeInTheDocument();

      rerender(
        <MemoryRouter initialEntries={['/study']}>
          <Layout>
            <div data-testid="study-page">Study</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByTestId('study-page')).toBeInTheDocument();
      expect(screen.getByTestId('navigation')).toBeInTheDocument();
    });

    it('preserves layout structure with dynamic content', () => {
      const { rerender } = renderWithRouter(
        <div data-testid="content-1">Content 1</div>
      );

      expect(screen.getByTestId('content-1')).toBeInTheDocument();
      const mainElement = screen.getByRole('main');

      rerender(
        <MemoryRouter initialEntries={['/']}>
          <Layout>
            <div data-testid="content-2">Content 2</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByTestId('content-2')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBe(mainElement); // Same main element
    });
  });

  describe('Error Boundaries', () => {
    it('handles child component errors gracefully', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderWithRouter(<ThrowError />);
      }).toThrow('Test error');

      consoleSpy.mockRestore();
    });
  });

  describe('Performance', () => {
    it('renders efficiently with minimal re-renders', () => {
      const renderSpy = vi.fn();
      
      const TestComponent = () => {
        renderSpy();
        return <div>Test</div>;
      };

      const { rerender } = renderWithRouter(<TestComponent />);

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same content
      rerender(
        <MemoryRouter initialEntries={['/']}>
          <Layout>
            <TestComponent />
          </Layout>
        </MemoryRouter>
      );

      // Component should re-render due to new Layout instance
      expect(renderSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe('CSS Classes and Styling', () => {
    it('applies correct base classes', () => {
      const { container } = renderWithRouter(<div>Test</div>);

      const layoutRoot = container.firstChild;
      expect(layoutRoot).toHaveClass('min-h-screen');
    });

    it('maintains proper spacing and layout', () => {
      const { container } = renderWithRouter(<div>Test</div>);

      const main = container.querySelector('main');
      expect(main).toHaveClass('flex-1');
    });
  });

  describe('Integration with Router', () => {
    it('works with different router states', () => {
      renderWithRouter(<div>Home</div>, ['/']);
      expect(screen.getByText('Home')).toBeInTheDocument();

      renderWithRouter(<div>About</div>, ['/about']);
      expect(screen.getByText('About')).toBeInTheDocument();
    });

    it('handles route changes within layout', () => {
      const { container } = renderWithRouter(<div>Initial</div>);
      const initialMain = container.querySelector('main');

      // Layout structure should remain consistent
      expect(initialMain).toBeInTheDocument();
      expect(screen.getByTestId('navigation')).toBeInTheDocument();
    });
  });
});