/**
 * Icon Size Utility System
 *
 * Provides standardized icon sizing utilities based on v3 UI design principles.
 * Establishes consistent size hierarchy and validation for icons across the application.
 */

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface IconProps {
  size?: IconSize;
  className?: string;
}

/**
 * Icon size mapping to Tailwind CSS classes
 */
export const ICON_SIZE_CLASSES: Record<IconSize, string> = {
  xs: 'w-3 h-3',    // 12px - For inline indicators, badges
  sm: 'w-4 h-4',    // 16px - For navigation, buttons, form elements
  md: 'w-5 h-5',    // 20px - For primary actions, important indicators
  lg: 'w-6 h-6',    // 24px - For section headers, feature highlights
  xl: 'w-8 h-8',    // 32px - For empty states, major status indicators
} as const;

/**
 * Context-based icon size recommendations
 */
export const ICON_CONTEXT_SIZES = {
  navigation: 'sm' as IconSize,
  button: 'sm' as IconSize,
  primaryButton: 'md' as IconSize,
  status: 'xs' as IconSize,
  statusImportant: 'sm' as IconSize,
  feature: 'md' as IconSize,
  featureHighlight: 'lg' as IconSize,
  emptyState: 'lg' as IconSize,
  emptyStateLarge: 'xl' as IconSize,
  loading: 'sm' as IconSize,
  loadingLarge: 'md' as IconSize,
} as const;

/**
 * Get the CSS class for a given icon size
 */
export function getIconSizeClass(size: IconSize): string {
  return ICON_SIZE_CLASSES[size];
}

/**
 * Get recommended icon size for a specific context
 */
export function getContextIconSize(context: keyof typeof ICON_CONTEXT_SIZES): IconSize {
  return ICON_CONTEXT_SIZES[context];
}

/**
 * Validate if a given size is a valid icon size
 */
export function isValidIconSize(size: string): size is IconSize {
  return Object.keys(ICON_SIZE_CLASSES).includes(size);
}

/**
 * Get all available icon sizes
 */
export function getAvailableIconSizes(): IconSize[] {
  return Object.keys(ICON_SIZE_CLASSES) as IconSize[];
}

/**
 * Combine icon size class with additional classes
 */
export function combineIconClasses(size: IconSize, additionalClasses?: string): string {
  const sizeClass = getIconSizeClass(size);
  return additionalClasses ? `${sizeClass} ${additionalClasses}` : sizeClass;
}

/**
 * Size validation helper for development
 */
export function validateIconSize(size: IconSize, context?: string): {
  isValid: boolean;
  warnings: string[];
} {
  const warnings: string[] = [];

  // Check if size is valid
  if (!isValidIconSize(size)) {
    return {
      isValid: false,
      warnings: [`Invalid icon size: ${size}. Valid sizes are: ${getAvailableIconSizes().join(', ')}`]
    };
  }

  // Context-specific warnings
  if (context) {
    switch (context) {
      case 'navigation':
        if (size !== 'sm') {
          warnings.push(`Navigation icons should typically use 'sm' size, but '${size}' was provided`);
        }
        break;
      case 'button':
        if (!['sm', 'md'].includes(size)) {
          warnings.push(`Button icons should typically use 'sm' or 'md' size, but '${size}' was provided`);
        }
        break;
      case 'empty-state':
        if (!['lg', 'xl'].includes(size)) {
          warnings.push(`Empty state icons should typically use 'lg' or 'xl' size, but '${size}' was provided`);
        }
        break;
    }
  }

  return {
    isValid: true,
    warnings
  };
}

/**
 * Helper to migrate from old size classes to new standardized sizes
 */
export function migrateIconSize(oldClass: string): IconSize | null {
  const migrationMap: Record<string, IconSize> = {
    'w-3 h-3': 'xs',
    'w-4 h-4': 'sm',
    'w-5 h-5': 'md',
    'w-6 h-6': 'lg',
    'w-8 h-8': 'xl',
    'w-10 h-10': 'lg', // Reduce oversized icons
    'w-12 h-12': 'xl', // Reduce oversized icons
  };

  return migrationMap[oldClass] || null;
}