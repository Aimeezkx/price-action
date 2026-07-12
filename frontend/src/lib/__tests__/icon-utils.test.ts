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

describe('Icon Utils', () => {
  describe('getIconSizeClass', () => {
    it('should return correct CSS class for each size', () => {
      expect(getIconSizeClass('xs')).toBe('w-3 h-3');
      expect(getIconSizeClass('sm')).toBe('w-4 h-4');
      expect(getIconSizeClass('md')).toBe('w-5 h-5');
      expect(getIconSizeClass('lg')).toBe('w-6 h-6');
      expect(getIconSizeClass('xl')).toBe('w-8 h-8');
    });
  });

  describe('getContextIconSize', () => {
    it('should return correct size for navigation context', () => {
      expect(getContextIconSize('navigation')).toBe('sm');
    });

    it('should return correct size for button context', () => {
      expect(getContextIconSize('button')).toBe('sm');
      expect(getContextIconSize('primaryButton')).toBe('md');
    });

    it('should return correct size for empty state context', () => {
      expect(getContextIconSize('emptyState')).toBe('lg');
      expect(getContextIconSize('emptyStateLarge')).toBe('xl');
    });

    it('should return correct size for status context', () => {
      expect(getContextIconSize('status')).toBe('xs');
      expect(getContextIconSize('statusImportant')).toBe('sm');
    });
  });

  describe('isValidIconSize', () => {
    it('should return true for valid icon sizes', () => {
      expect(isValidIconSize('xs')).toBe(true);
      expect(isValidIconSize('sm')).toBe(true);
      expect(isValidIconSize('md')).toBe(true);
      expect(isValidIconSize('lg')).toBe(true);
      expect(isValidIconSize('xl')).toBe(true);
    });

    it('should return false for invalid icon sizes', () => {
      expect(isValidIconSize('xxl')).toBe(false);
      expect(isValidIconSize('tiny')).toBe(false);
      expect(isValidIconSize('')).toBe(false);
      expect(isValidIconSize('invalid')).toBe(false);
    });
  });

  describe('getAvailableIconSizes', () => {
    it('should return all available icon sizes', () => {
      const sizes = getAvailableIconSizes();
      expect(sizes).toEqual(['xs', 'sm', 'md', 'lg', 'xl']);
    });
  });

  describe('combineIconClasses', () => {
    it('should return only size class when no additional classes provided', () => {
      expect(combineIconClasses('sm')).toBe('w-4 h-4');
    });

    it('should combine size class with additional classes', () => {
      expect(combineIconClasses('sm', 'text-blue-500')).toBe('w-4 h-4 text-blue-500');
      expect(combineIconClasses('lg', 'text-red-500 hover:text-red-600')).toBe('w-6 h-6 text-red-500 hover:text-red-600');
    });
  });

  describe('validateIconSize', () => {
    it('should validate valid icon sizes without warnings', () => {
      const result = validateIconSize('sm');
      expect(result.isValid).toBe(true);
      expect(result.warnings).toEqual([]);
    });

    it('should return invalid for invalid sizes', () => {
      const result = validateIconSize('invalid' as IconSize);
      expect(result.isValid).toBe(false);
      expect(result.warnings).toContain('Invalid icon size: invalid. Valid sizes are: xs, sm, md, lg, xl');
    });

    it('should provide context-specific warnings for navigation', () => {
      const result = validateIconSize('xl', 'navigation');
      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain("Navigation icons should typically use 'sm' size, but 'xl' was provided");
    });

    it('should provide context-specific warnings for buttons', () => {
      const result = validateIconSize('xl', 'button');
      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain("Button icons should typically use 'sm' or 'md' size, but 'xl' was provided");
    });

    it('should provide context-specific warnings for empty states', () => {
      const result = validateIconSize('xs', 'empty-state');
      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain("Empty state icons should typically use 'lg' or 'xl' size, but 'xs' was provided");
    });

    it('should not provide warnings for appropriate context sizes', () => {
      expect(validateIconSize('sm', 'navigation').warnings).toEqual([]);
      expect(validateIconSize('sm', 'button').warnings).toEqual([]);
      expect(validateIconSize('md', 'button').warnings).toEqual([]);
      expect(validateIconSize('lg', 'empty-state').warnings).toEqual([]);
      expect(validateIconSize('xl', 'empty-state').warnings).toEqual([]);
    });
  });

  describe('migrateIconSize', () => {
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
  });

  describe('ICON_SIZE_CLASSES constant', () => {
    it('should have all required size mappings', () => {
      expect(ICON_SIZE_CLASSES).toEqual({
        xs: 'w-3 h-3',
        sm: 'w-4 h-4',
        md: 'w-5 h-5',
        lg: 'w-6 h-6',
        xl: 'w-8 h-8',
      });
    });
  });

  describe('ICON_CONTEXT_SIZES constant', () => {
    it('should have all required context mappings', () => {
      expect(ICON_CONTEXT_SIZES.navigation).toBe('sm');
      expect(ICON_CONTEXT_SIZES.button).toBe('sm');
      expect(ICON_CONTEXT_SIZES.primaryButton).toBe('md');
      expect(ICON_CONTEXT_SIZES.status).toBe('xs');
      expect(ICON_CONTEXT_SIZES.statusImportant).toBe('sm');
      expect(ICON_CONTEXT_SIZES.feature).toBe('md');
      expect(ICON_CONTEXT_SIZES.featureHighlight).toBe('lg');
      expect(ICON_CONTEXT_SIZES.emptyState).toBe('lg');
      expect(ICON_CONTEXT_SIZES.emptyStateLarge).toBe('xl');
      expect(ICON_CONTEXT_SIZES.loading).toBe('sm');
      expect(ICON_CONTEXT_SIZES.loadingLarge).toBe('md');
    });
  });
});