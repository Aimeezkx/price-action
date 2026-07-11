import {
  getIconProps,
  getContextIconProps,
  createIconClass,
  suggestIconMigration,
} from '../icon-component-helpers';

import { vi } from 'vitest';

// Mock console.warn for development warnings
const mockConsoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});

describe('Icon Component Helpers', () => {
  beforeEach(() => {
    mockConsoleWarn.mockClear();
  });

  afterAll(() => {
    mockConsoleWarn.mockRestore();
  });

  describe('getIconProps', () => {
    it('should return props with default small size', () => {
      const props = getIconProps();
      expect(props).toEqual({
        className: 'w-4 h-4',
        'data-icon-size': 'sm',
      });
    });

    it('should return props with specified size', () => {
      const props = getIconProps('lg');
      expect(props).toEqual({
        className: 'w-6 h-6',
        'data-icon-size': 'lg',
      });
    });

    it('should include context in props when provided', () => {
      const props = getIconProps('sm', 'navigation');
      expect(props).toEqual({
        className: 'w-4 h-4',
        'data-icon-size': 'sm',
        'data-icon-context': 'navigation',
      });
    });

    it('should combine additional classes', () => {
      const props = getIconProps('md', undefined, 'text-blue-500');
      expect(props).toEqual({
        className: 'w-5 h-5 text-blue-500',
        'data-icon-size': 'md',
      });
    });

    describe('development warnings', () => {
      const originalEnv = process.env.NODE_ENV;

      beforeEach(() => {
        process.env.NODE_ENV = 'development';
      });

      afterEach(() => {
        process.env.NODE_ENV = originalEnv;
      });

      it('should warn for inappropriate context usage', () => {
        getIconProps('xl', 'navigation');
        expect(mockConsoleWarn).toHaveBeenCalledWith(
          'Icon validation warnings for context "navigation":',
          ["Navigation icons should typically use 'sm' size, but 'xl' was provided"]
        );
      });

      it('should not warn for appropriate context usage', () => {
        getIconProps('sm', 'navigation');
        expect(mockConsoleWarn).not.toHaveBeenCalled();
      });
    });
  });

  describe('getContextIconProps', () => {
    it('should return props for navigation context', () => {
      const props = getContextIconProps('navigation');
      expect(props).toEqual({
        className: 'w-4 h-4',
        'data-icon-size': 'sm',
        'data-icon-context': 'navigation',
      });
    });

    it('should return props for button context', () => {
      const props = getContextIconProps('button');
      expect(props).toEqual({
        className: 'w-4 h-4',
        'data-icon-size': 'sm',
        'data-icon-context': 'button',
      });
    });

    it('should return props for primary button context', () => {
      const props = getContextIconProps('primaryButton');
      expect(props).toEqual({
        className: 'w-5 h-5',
        'data-icon-size': 'md',
        'data-icon-context': 'primaryButton',
      });
    });

    it('should return props for empty state context', () => {
      const props = getContextIconProps('emptyState');
      expect(props).toEqual({
        className: 'w-6 h-6',
        'data-icon-size': 'lg',
        'data-icon-context': 'emptyState',
      });
    });

    it('should combine with additional classes', () => {
      const props = getContextIconProps('status', 'text-green-500');
      expect(props).toEqual({
        className: 'w-3 h-3 text-green-500',
        'data-icon-size': 'xs',
        'data-icon-context': 'status',
      });
    });
  });

  describe('createIconClass', () => {
    it('should create class string for size only', () => {
      expect(createIconClass('sm')).toBe('w-4 h-4');
      expect(createIconClass('lg')).toBe('w-6 h-6');
    });

    it('should combine size with additional classes', () => {
      expect(createIconClass('md', 'text-blue-500')).toBe('w-5 h-5 text-blue-500');
      expect(createIconClass('xs', 'text-red-500 hover:text-red-600')).toBe('w-3 h-3 text-red-500 hover:text-red-600');
    });
  });

  describe('suggestIconMigration', () => {
    it('should suggest migration for standard sizes', () => {
      const result = suggestIconMigration('w-4 h-4 text-blue-500');
      expect(result).toEqual({
        suggestedSize: 'sm',
        suggestedClasses: 'w-4 h-4 text-blue-500',
        warnings: [],
      });
    });

    it('should suggest migration for oversized icons', () => {
      const result = suggestIconMigration('w-12 h-12 text-red-500');
      expect(result).toEqual({
        suggestedSize: 'xl',
        suggestedClasses: 'w-8 h-8 text-red-500',
        warnings: [],
      });
    });

    it('should reduce w-10 h-10 to lg', () => {
      const result = suggestIconMigration('w-10 h-10');
      expect(result).toEqual({
        suggestedSize: 'lg',
        suggestedClasses: 'w-6 h-6',
        warnings: [],
      });
    });

    it('should handle context-specific suggestions', () => {
      const result = suggestIconMigration('w-8 h-8', 'navigation');
      expect(result.suggestedSize).toBe('sm');
      expect(result.suggestedClasses).toBe('w-4 h-4');
      expect(result.warnings).toContain('Context "navigation" typically uses "sm" but "xl" was suggested based on current size');
    });

    it('should handle unknown size patterns', () => {
      const result = suggestIconMigration('w-20 h-20 text-gray-500');
      expect(result.suggestedSize).toBe('sm'); // Default fallback
      expect(result.suggestedClasses).toBe('w-4 h-4 text-gray-500');
      expect(result.warnings).toContain('Unknown size pattern: w-20 h-20');
    });

    it('should handle classes without size patterns', () => {
      const result = suggestIconMigration('text-blue-500 hover:text-blue-600');
      expect(result.suggestedSize).toBe('sm');
      expect(result.suggestedClasses).toBe('w-4 h-4 text-blue-500 hover:text-blue-600');
      expect(result.warnings).toContain('No size classes found in current classes');
    });

    it('should use context-appropriate size when no size found', () => {
      const result = suggestIconMigration('text-blue-500', 'emptyState');
      expect(result.suggestedSize).toBe('lg');
      expect(result.suggestedClasses).toBe('w-6 h-6 text-blue-500');
    });

    it('should preserve other classes while replacing size', () => {
      const result = suggestIconMigration('w-12 h-12 text-blue-500 hover:text-blue-600 transition-colors');
      expect(result.suggestedClasses).toBe('w-8 h-8 text-blue-500 hover:text-blue-600 transition-colors');
    });
  });
});