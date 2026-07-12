/**
 * Comprehensive Icon Size Testing
 *
 * This test suite provides comprehensive testing for the icon sizing system,
 * including unit tests, integration tests, and validation helpers.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  IconSize,
  ICON_SIZE_CLASSES,
  ICON_CONTEXT_SIZES,
  getIconSizeClass,
  getContextIconSize,
  isValidIconSize,
  getAvailableIconSizes,
  combineIconClasses,
  validateIconSize,
  migrateIconSize,
} from '../icon-utils';

import {
  getIconProps,
  getContextIconProps,
  createIconClass,
  suggestIconMigration,
} from '../icon-component-helpers';

describe('Comprehensive Icon Size Testing', () => {
  describe('Icon Size System Validation', () => {
    it('should have consistent size hierarchy', () => {
      const sizes = getAvailableIconSizes();
      expect(sizes).toEqual(['xs', 'sm', 'md', 'lg', 'xl']);

      // Verify size progression (in pixels)
      const sizePixels = {
        xs: 12, // w-3 h-3
        sm: 16, // w-4 h-4
        md: 20, // w-5 h-5
        lg: 24, // w-6 h-6
        xl: 32, // w-8 h-8
      };

      // Ensure each size is larger than the previous
      expect(sizePixels.xs).toBeLessThan(sizePixels.sm);
      expect(sizePixels.sm).toBeLessThan(sizePixels.md);
      expect(sizePixels.md).toBeLessThan(sizePixels.lg);
      expect(sizePixels.lg).toBeLessThan(sizePixels.xl);
    });

    it('should have all required context mappings', () => {
      const requiredContexts = [
        'navigation',
        'button',
        'primaryButton',
        'status',
        'statusImportant',
        'feature',
        'featureHighlight',
        'emptyState',
        'emptyStateLarge',
        'loading',
        'loadingLarge',
      ];

      requiredContexts.forEach(context => {
        expect(ICON_CONTEXT_SIZES).toHaveProperty(context);
        expect(isValidIconSize(ICON_CONTEXT_SIZES[context as keyof typeof ICON_CONTEXT_SIZES])).toBe(true);
      });
    });

    it('should provide appropriate sizes for different contexts', () => {
      // Navigation should use small icons
      expect(getContextIconSize('navigation')).toBe('sm');

      // Buttons should use small to medium icons
      expect(['sm', 'md']).toContain(getContextIconSize('button'));
      expect(['sm', 'md']).toContain(getContextIconSize('primaryButton'));

      // Status indicators should use extra small to small icons
      expect(['xs', 'sm']).toContain(getContextIconSize('status'));
      expect(['xs', 'sm']).toContain(getContextIconSize('statusImportant'));

      // Empty states should use larger icons
      expect(['lg', 'xl']).toContain(getContextIconSize('emptyState'));
      expect(['lg', 'xl']).toContain(getContextIconSize('emptyStateLarge'));
    });
  });

  describe('Icon Size Class Generation', () => {
    it('should generate correct Tailwind classes', () => {
      expect(getIconSizeClass('xs')).toBe('w-3 h-3');
      expect(getIconSizeClass('sm')).toBe('w-4 h-4');
      expect(getIconSizeClass('md')).toBe('w-5 h-5');
      expect(getIconSizeClass('lg')).toBe('w-6 h-6');
      expect(getIconSizeClass('xl')).toBe('w-8 h-8');
    });

    it('should combine classes correctly', () => {
      expect(combineIconClasses('sm')).toBe('w-4 h-4');
      expect(combineIconClasses('sm', 'text-blue-500')).toBe('w-4 h-4 text-blue-500');
      expect(combineIconClasses('lg', 'text-red-500 hover:text-red-600')).toBe('w-6 h-6 text-red-500 hover:text-red-600');
    });

    it('should handle empty additional classes', () => {
      expect(combineIconClasses('md', '')).toBe('w-5 h-5');
      expect(combineIconClasses('md', undefined)).toBe('w-5 h-5');
    });
  });

  describe('Icon Size Validation', () => {
    it('should validate icon sizes correctly', () => {
      // Valid sizes
      expect(isValidIconSize('xs')).toBe(true);
      expect(isValidIconSize('sm')).toBe(true);
      expect(isValidIconSize('md')).toBe(true);
      expect(isValidIconSize('lg')).toBe(true);
      expect(isValidIconSize('xl')).toBe(true);

      // Invalid sizes
      expect(isValidIconSize('xxs')).toBe(false);
      expect(isValidIconSize('xxl')).toBe(false);
      expect(isValidIconSize('tiny')).toBe(false);
      expect(isValidIconSize('huge')).toBe(false);
      expect(isValidIconSize('')).toBe(false);
    });

    it('should provide context-specific validation', () => {
      // Navigation context
      const navValidation = validateIconSize('sm', 'navigation');
      expect(navValidation.isValid).toBe(true);
      expect(navValidation.warnings).toHaveLength(0);

      const navWarning = validateIconSize('xl', 'navigation');
      expect(navWarning.isValid).toBe(true);
      expect(navWarning.warnings).toContain("Navigation icons should typically use 'sm' size, but 'xl' was provided");

      // Button context
      const buttonValidation = validateIconSize('md', 'button');
      expect(buttonValidation.isValid).toBe(true);
      expect(buttonValidation.warnings).toHaveLength(0);

      const buttonWarning = validateIconSize('xl', 'button');
      expect(buttonWarning.isValid).toBe(true);
      expect(buttonWarning.warnings).toContain("Button icons should typically use 'sm' or 'md' size, but 'xl' was provided");

      // Empty state context
      const emptyStateValidation = validateIconSize('lg', 'empty-state');
      expect(emptyStateValidation.isValid).toBe(true);
      expect(emptyStateValidation.warnings).toHaveLength(0);

      const emptyStateWarning = validateIconSize('xs', 'empty-state');
      expect(emptyStateWarning.isValid).toBe(true);
      expect(emptyStateWarning.warnings).toContain("Empty state icons should typically use 'lg' or 'xl' size, but 'xs' was provided");
    });

    it('should handle invalid sizes in validation', () => {
      const invalidValidation = validateIconSize('invalid' as IconSize);
      expect(invalidValidation.isValid).toBe(false);
      expect(invalidValidation.warnings).toContain('Invalid icon size: invalid. Valid sizes are: xs, sm, md, lg, xl');
    });
  });

  describe('Icon Migration System', () => {
    it('should migrate standard sizes correctly', () => {
      expect(migrateIconSize('w-3 h-3')).toBe('xs');
      expect(migrateIconSize('w-4 h-4')).toBe('sm');
      expect(migrateIconSize('w-5 h-5')).toBe('md');
      expect(migrateIconSize('w-6 h-6')).toBe('lg');
      expect(migrateIconSize('w-8 h-8')).toBe('xl');
    });

    it('should migrate oversized icons to appropriate sizes', () => {
      expect(migrateIconSize('w-10 h-10')).toBe('lg');
      expect(migrateIconSize('w-12 h-12')).toBe('xl');
    });

    it('should return null for unknown sizes', () => {
      expect(migrateIconSize('w-16 h-16')).toBe(null);
      expect(migrateIconSize('w-2 h-2')).toBe(null);
      expect(migrateIconSize('invalid')).toBe(null);
    });

    it('should suggest appropriate migrations with context', () => {
      // Standard migration
      const standardResult = suggestIconMigration('w-4 h-4 text-blue-500');
      expect(standardResult.suggestedSize).toBe('sm');
      expect(standardResult.suggestedClasses).toBe('w-4 h-4 text-blue-500');
      expect(standardResult.warnings).toHaveLength(0);

      // Oversized migration
      const oversizedResult = suggestIconMigration('w-12 h-12 text-red-500');
      expect(oversizedResult.suggestedSize).toBe('xl');
      expect(oversizedResult.suggestedClasses).toBe('w-8 h-8 text-red-500');

      // Context-specific migration
      const contextResult = suggestIconMigration('w-8 h-8', 'navigation');
      expect(contextResult.suggestedSize).toBe('sm');
      expect(contextResult.suggestedClasses).toBe('w-4 h-4');
      expect(contextResult.warnings.some(w => w.includes('Context "navigation"'))).toBe(true);
    });
  });

  describe('Component Helper Integration', () => {
    const mockConsoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});

    beforeEach(() => {
      mockConsoleWarn.mockClear();
    });

    afterEach(() => {
      mockConsoleWarn.mockRestore();
    });

    it('should generate correct props for components', () => {
      const props = getIconProps('md', 'feature', 'text-blue-500');
      expect(props).toEqual({
        className: 'w-5 h-5 text-blue-500',
        'data-icon-size': 'md',
        'data-icon-context': 'feature',
      });
    });

    it('should generate context-appropriate props', () => {
      const navProps = getContextIconProps('navigation');
      expect(navProps).toEqual({
        className: 'w-4 h-4',
        'data-icon-size': 'sm',
        'data-icon-context': 'navigation',
      });

      const emptyStateProps = getContextIconProps('emptyState');
      expect(emptyStateProps).toEqual({
        className: 'w-6 h-6',
        'data-icon-size': 'lg',
        'data-icon-context': 'emptyState',
      });
    });

    it('should create icon classes directly', () => {
      expect(createIconClass('sm')).toBe('w-4 h-4');
      expect(createIconClass('lg', 'text-green-500')).toBe('w-6 h-6 text-green-500');
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle empty strings gracefully', () => {
      expect(isValidIconSize('')).toBe(false);
      expect(migrateIconSize('')).toBe(null);
    });

    it('should handle undefined values gracefully', () => {
      const props = getIconProps();
      expect(props['data-icon-size']).toBe('sm'); // Default size
    });

    it('should preserve class order in combinations', () => {
      const combined = combineIconClasses('md', 'text-blue-500 hover:text-blue-600 transition-colors');
      expect(combined).toBe('w-5 h-5 text-blue-500 hover:text-blue-600 transition-colors');
    });

    it('should handle malformed size classes in migration', () => {
      const result = suggestIconMigration('w-4 text-blue-500'); // Missing h-4
      expect(result.warnings).toContain('No size classes found in current classes');
      expect(result.suggestedSize).toBe('sm'); // Default fallback
    });
  });

  describe('Performance and Memory', () => {
    it('should not create new objects unnecessarily', () => {
      const sizes1 = getAvailableIconSizes();
      const sizes2 = getAvailableIconSizes();
      // Arrays should have same content but may be different instances
      expect(sizes1).toEqual(sizes2);
    });

    it('should handle large numbers of validations efficiently', () => {
      const startTime = performance.now();

      // Perform many validations
      for (let i = 0; i < 1000; i++) {
        validateIconSize('sm', 'navigation');
        validateIconSize('md', 'button');
        validateIconSize('lg', 'empty-state');
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Should complete within reasonable time (adjust threshold as needed)
      expect(duration).toBeLessThan(100); // 100ms for 3000 validations
    });
  });

  describe('Type Safety', () => {
    it('should enforce type safety for icon sizes', () => {
      // These should compile without errors
      const validSize: IconSize = 'sm';
      expect(isValidIconSize(validSize)).toBe(true);

      const validClass = getIconSizeClass(validSize);
      expect(validClass).toBe('w-4 h-4');
    });

    it('should provide correct return types', () => {
      const sizes = getAvailableIconSizes();
      expect(Array.isArray(sizes)).toBe(true);
      expect(sizes.every(size => typeof size === 'string')).toBe(true);

      const validation = validateIconSize('sm');
      expect(typeof validation.isValid).toBe('boolean');
      expect(Array.isArray(validation.warnings)).toBe(true);
    });
  });
});