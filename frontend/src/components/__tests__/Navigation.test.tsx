import React from 'react';
import { render, screen } from '../../../test/utils';
import { MemoryRouter } from 'react-router-dom';
import { Navigation } from '../Navigation';

// Custom render function with router
const renderWithRouter = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Navigation />
    </MemoryRouter>
  );
};

describe('Navigation', () => {
  describe('Basic Rendering', () => {
    it('renders app title', () => {
      renderWithRouter();

      expect(screen.getByText('Document Learning App')).toBeInTheDocument();
    });

    it('renders all navigation items', () => {
      renderWithRouter();

      expect(screen.getByText('Documents')).toBeInTheDocument();
      expect(screen.getByText('Study')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('Export')).toBeInTheDocument();
      expect(screen.getByText('Privacy')).toBeInTheDocument();
    });

    it('has correct navigation structure', () => {
      renderWithRouter();

      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
  });

  describe('Navigation Links', () => {
    it('has correct href attributes for all links', () => {
      renderWithRouter();

      expect(screen.getByRole('link', { name: 'Document Learning App' })).toHaveAttribute('href', '/');
      expect(screen.getByRole('link', { name: 'Documents' })).toHaveAttribute('href', '/documents');
      expect(screen.getByRole('link', { name: 'Study' })).toHaveAttribute('href', '/study');
      expect(screen.getByRole('link', { name: 'Search' })).toHaveAttribute('href', '/search');
      expect(screen.getByRole('link', { name: 'Export' })).toHaveAttribute('href', '/export');
      expect(screen.getByRole('link', { name: 'Privacy' })).toHaveAttribute('href', '/privacy');
    });

    it('renders both desktop and mobile navigation items', () => {
      renderWithRouter();

      // Desktop navigation (hidden on mobile)
      const desktopNavItems = screen.getAllByText('Documents');
      expect(desktopNavItems).toHaveLength(2); // One for desktop, one for mobile

      const desktopStudyItems = screen.getAllByText('Study');
      expect(desktopStudyItems).toHaveLength(2);
    });
  });

  describe('Active State Highlighting', () => {
    it('highlights Documents link when on documents page', () => {
      renderWithRouter(['/documents']);

      const desktopDocumentsLink = screen.getAllByRole('link', { name: 'Documents' })[0];
      expect(desktopDocumentsLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('highlights Study link when on study page', () => {
      renderWithRouter(['/study']);

      const desktopStudyLink = screen.getAllByRole('link', { name: 'Study' })[0];
      expect(desktopStudyLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('highlights Search link when on search page', () => {
      renderWithRouter(['/search']);

      const desktopSearchLink = screen.getAllByRole('link', { name: 'Search' })[0];
      expect(desktopSearchLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('highlights Export link when on export page', () => {
      renderWithRouter(['/export']);

      const desktopExportLink = screen.getAllByRole('link', { name: 'Export' })[0];
      expect(desktopExportLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('highlights Privacy link when on privacy page', () => {
      renderWithRouter(['/privacy']);

      const desktopPrivacyLink = screen.getAllByRole('link', { name: 'Privacy' })[0];
      expect(desktopPrivacyLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('shows inactive styling for non-active links', () => {
      renderWithRouter(['/documents']);

      const desktopStudyLink = screen.getAllByRole('link', { name: 'Study' })[0];
      expect(desktopStudyLink).toHaveClass('border-transparent', 'text-gray-500');
    });
  });

  describe('Mobile Navigation', () => {
    it('shows mobile navigation menu', () => {
      renderWithRouter();

      // Mobile navigation should be present but hidden by default (sm:hidden)
      const mobileNavItems = screen.getAllByText('Documents');
      expect(mobileNavItems[1]).toBeInTheDocument(); // Second one is mobile
    });

    it('applies correct mobile styling for active items', () => {
      renderWithRouter(['/documents']);

      const mobileDocumentsLink = screen.getAllByRole('link', { name: 'Documents' })[1];
      expect(mobileDocumentsLink).toHaveClass('bg-blue-50', 'border-blue-500', 'text-blue-700');
    });

    it('applies correct mobile styling for inactive items', () => {
      renderWithRouter(['/documents']);

      const mobileStudyLink = screen.getAllByRole('link', { name: 'Study' })[1];
      expect(mobileStudyLink).toHaveClass('border-transparent', 'text-gray-500');
    });
  });

  describe('Responsive Design', () => {
    it('has responsive classes for desktop navigation', () => {
      renderWithRouter();

      const desktopNav = screen.getAllByText('Documents')[0].closest('.hidden');
      expect(desktopNav).toHaveClass('sm:ml-6', 'sm:flex', 'sm:space-x-8');
    });

    it('has responsive classes for mobile navigation', () => {
      renderWithRouter();

      const mobileNav = screen.getAllByText('Documents')[1].closest('.sm\\:hidden');
      expect(mobileNav).toHaveClass('sm:hidden');
    });
  });

  describe('Hover States', () => {
    it('applies hover classes to inactive desktop links', () => {
      renderWithRouter(['/documents']);

      const desktopStudyLink = screen.getAllByRole('link', { name: 'Study' })[0];
      expect(desktopStudyLink).toHaveClass('hover:border-gray-300', 'hover:text-gray-700');
    });

    it('applies hover classes to inactive mobile links', () => {
      renderWithRouter(['/documents']);

      const mobileStudyLink = screen.getAllByRole('link', { name: 'Study' })[1];
      expect(mobileStudyLink).toHaveClass('hover:bg-gray-50', 'hover:border-gray-300', 'hover:text-gray-700');
    });
  });

  describe('Accessibility', () => {
    it('has proper navigation landmark', () => {
      renderWithRouter();

      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('all navigation items are accessible links', () => {
      renderWithRouter();

      const allLinks = screen.getAllByRole('link');
      expect(allLinks.length).toBeGreaterThan(0);
      
      // Check that each link has proper href
      allLinks.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });

    it('app title link is accessible', () => {
      renderWithRouter();

      const titleLink = screen.getByRole('link', { name: 'Document Learning App' });
      expect(titleLink).toBeInTheDocument();
      expect(titleLink).toHaveAttribute('href', '/');
    });
  });

  describe('Nested Routes', () => {
    it('highlights parent route for nested paths', () => {
      renderWithRouter(['/documents/123']);

      const desktopDocumentsLink = screen.getAllByRole('link', { name: 'Documents' })[0];
      expect(desktopDocumentsLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('highlights search for search results page', () => {
      renderWithRouter(['/search/results']);

      const desktopSearchLink = screen.getAllByRole('link', { name: 'Search' })[0];
      expect(desktopSearchLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('highlights study for review session', () => {
      renderWithRouter(['/study/review']);

      const desktopStudyLink = screen.getAllByRole('link', { name: 'Study' })[0];
      expect(desktopStudyLink).toHaveClass('border-blue-500', 'text-gray-900');
    });
  });

  describe('Edge Cases', () => {
    it('handles root path correctly', () => {
      renderWithRouter(['/']);

      // No navigation item should be active on root path
      const desktopLinks = screen.getAllByRole('link').slice(1, 6); // Skip title link
      desktopLinks.forEach(link => {
        expect(link).toHaveClass('border-transparent');
      });
    });

    it('handles unknown paths gracefully', () => {
      renderWithRouter(['/unknown-path']);

      // Should render without errors
      expect(screen.getByText('Document Learning App')).toBeInTheDocument();
      
      // No navigation item should be active
      const desktopLinks = screen.getAllByRole('link').slice(1, 6);
      desktopLinks.forEach(link => {
        expect(link).toHaveClass('border-transparent');
      });
    });

    it('handles paths with query parameters', () => {
      renderWithRouter(['/documents?page=2']);

      const desktopDocumentsLink = screen.getAllByRole('link', { name: 'Documents' })[0];
      expect(desktopDocumentsLink).toHaveClass('border-blue-500', 'text-gray-900');
    });

    it('handles paths with hash fragments', () => {
      renderWithRouter(['/search#results']);

      const desktopSearchLink = screen.getAllByRole('link', { name: 'Search' })[0];
      expect(desktopSearchLink).toHaveClass('border-blue-500', 'text-gray-900');
    });
  });

  describe('Visual Consistency', () => {
    it('maintains consistent spacing and typography', () => {
      renderWithRouter();

      const desktopLinks = screen.getAllByRole('link').slice(1, 6);
      desktopLinks.forEach(link => {
        expect(link).toHaveClass('text-sm', 'font-medium');
      });
    });

    it('maintains consistent mobile layout', () => {
      renderWithRouter();

      const mobileLinks = screen.getAllByRole('link').slice(6); // Mobile links come after desktop
      mobileLinks.forEach(link => {
        expect(link).toHaveClass('text-base', 'font-medium');
      });
    });
  });
});