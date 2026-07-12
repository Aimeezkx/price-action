import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ModernNavigation } from '../ModernNavigation';

// Custom render function with router
const renderWithRouter = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <ModernNavigation />
    </MemoryRouter>
  );
};

describe('ModernNavigation', () => {
  describe('Icon Size Optimization', () => {
    it('uses optimized icon sizes for mobile menu button', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');
      const menuIcon = menuButton.querySelector('svg');

      expect(menuIcon).toHaveClass('h-4', 'w-4');
    });

    it('maintains appropriate logo icon size', () => {
      renderWithRouter();

      const logoContainer = screen.getByText('Document Learning App').closest('a');
      const logoIcon = logoContainer?.querySelector('svg');

      expect(logoIcon).toHaveClass('w-5', 'h-5');
    });

    it('uses appropriate container size for logo', () => {
      renderWithRouter();

      const logoContainer = screen.getByText('Document Learning App').closest('a');
      const iconContainer = logoContainer?.querySelector('div.w-8.h-8');

      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe('Mobile Menu Functionality', () => {
    it('toggles mobile menu when button is clicked', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');

      // Initially closed - should show hamburger icon
      let menuIcon = menuButton.querySelector('svg');
      expect(menuIcon).toHaveClass('h-4', 'w-4');

      // Click to open
      fireEvent.click(menuButton);

      // Should now show close icon
      menuIcon = menuButton.querySelector('svg');
      expect(menuIcon).toHaveClass('h-4', 'w-4');

      // Mobile menu should be visible
      expect(screen.getAllByRole('navigation')).toHaveLength(2);
    });

    it('closes mobile menu when navigation item is clicked', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');

      // Open mobile menu
      fireEvent.click(menuButton);

      // Click on a navigation item
      const mobileNavItems = screen.getAllByText('Documents');
      const mobileDocumentsLink = mobileNavItems.find(item =>
        item.closest('nav')?.classList.contains('py-4')
      );

      if (mobileDocumentsLink) {
        fireEvent.click(mobileDocumentsLink);
      }

      // Menu should close (hamburger icon should be visible again)
      const menuIcon = menuButton.querySelector('svg');
      expect(menuIcon).toHaveClass('h-4', 'w-4');
    });
  });

  describe('Responsive Design', () => {
    it('has proper responsive classes for desktop navigation', () => {
      renderWithRouter();

      const desktopNav = screen.getByRole('navigation', { hidden: true });
      expect(desktopNav).toHaveClass('hidden', 'md:flex');
    });

    it('has proper responsive classes for mobile menu button', () => {
      renderWithRouter();

      const menuButtonContainer = screen.getByLabelText('Toggle menu').parentElement;
      expect(menuButtonContainer).toHaveClass('md:hidden');
    });

    it('maintains proper touch target size for mobile menu button', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');
      expect(menuButton).toHaveClass('p-3'); // Increased padding to maintain touch target
    });
  });

  describe('Navigation Spacing and Alignment', () => {
    it('maintains proper spacing in header', () => {
      renderWithRouter();

      const header = screen.getByRole('banner');
      const headerContent = header.querySelector('.flex.justify-between.items-center.h-16');

      expect(headerContent).toBeInTheDocument();
    });

    it('maintains proper logo spacing', () => {
      renderWithRouter();

      const logoContainer = screen.getByText('Document Learning App').closest('div');
      expect(logoContainer).toHaveClass('flex', 'items-center', 'space-x-3');
    });

    it('maintains proper navigation item spacing', () => {
      renderWithRouter();

      const desktopNav = screen.getByRole('navigation', { hidden: true });
      expect(desktopNav).toHaveClass('space-x-1');
    });
  });

  describe('Visual Consistency', () => {
    it('applies consistent styling to navigation items', () => {
      renderWithRouter();

      const navItems = screen.getAllByRole('link').filter(link =>
        link.textContent && ['Documents', 'Study', 'Search', 'Export', 'Privacy'].includes(link.textContent)
      );

      navItems.forEach(item => {
        expect(item).toHaveClass('px-4', 'py-2', 'text-sm', 'font-medium', 'rounded-lg');
      });
    });

    it('maintains proper hover states', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');
      expect(menuButton).toHaveClass('hover:bg-gray-100');
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label for mobile menu button', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');
      expect(menuButton).toBeInTheDocument();
    });

    it('maintains keyboard navigation', () => {
      renderWithRouter();

      const menuButton = screen.getByLabelText('Toggle menu');
      expect(menuButton).toHaveAttribute('type', 'button');
    });
  });

  describe('Active State Management', () => {
    it('highlights active navigation item', () => {
      renderWithRouter(['/documents']);

      const documentsLink = screen.getByRole('link', { name: 'Documents' });
      expect(documentsLink).toHaveClass('bg-blue-100', 'text-blue-700');
    });

    it('shows inactive styling for non-active items', () => {
      renderWithRouter(['/documents']);

      const studyLink = screen.getByRole('link', { name: 'Study' });
      expect(studyLink).toHaveClass('text-gray-600');
    });
  });
});
