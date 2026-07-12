/**
 * Icon Component Helpers
 *
 * Utility functions to help apply standardized icon sizing to existing components
 * without requiring a wrapper component.
 */

import { IconSize } from '../types';
import { combineIconClasses, validateIconSize, getContextIconSize } from './icon-utils';

/**
 * Props interface for icon components that support standardized sizing
 */
export interface StandardIconProps {
  size?: IconSize;
  context?: string;
  className?: string;
}

/**
 * Generate props for an icon component with standardized sizing
 *
 * @param size - The icon size to use
 * @param context - Optional context for validation
 * @param additionalClasses - Additional CSS classes
 * @returns Object with className and data attributes
 */
export function getIconProps(
  size: IconSize = 'sm',
  context?: string,
  additionalClasses?: string
): {
  className: string;
  'data-icon-size': IconSize;
  'data-icon-context'?: string;
} {
  // Development-only validation
  if (process.env.NODE_ENV === 'development' && context) {
    const validation = validateIconSize(size, context);
    if (validation.warnings.length > 0) {
      console.warn(`Icon validation warnings for context "${context}":`, validation.warnings);
    }
  }

  const props: {
    className: string;
    'data-icon-size': IconSize;
    'data-icon-context'?: string;
  } = {
    className: combineIconClasses(size, additionalClasses),
    'data-icon-size': size,
  };

  if (context) {
    props['data-icon-context'] = context;
  }

  return props;
}

/**
 * Generate props for an icon based on its context
 *
 * @param context - The context to get recommended size for
 * @param additionalClasses - Additional CSS classes
 * @returns Object with className and data attributes
 */
export function getContextIconProps(
  context: keyof typeof import('./icon-utils').ICON_CONTEXT_SIZES,
  additionalClasses?: string
): {
  className: string;
  'data-icon-size': IconSize;
  'data-icon-context': string;
} {
  const size = getContextIconSize(context);
  return {
    className: combineIconClasses(size, additionalClasses),
    'data-icon-size': size,
    'data-icon-context': context,
  };
}

/**
 * Create a standardized icon class string for direct use
 *
 * @param size - The icon size
 * @param additionalClasses - Additional CSS classes
 * @returns Combined class string
 */
export function createIconClass(size: IconSize, additionalClasses?: string): string {
  return combineIconClasses(size, additionalClasses);
}

/**
 * Utility to help migrate existing icon usage
 *
 * @param currentClasses - Current CSS classes
 * @param context - Context for the icon
 * @returns Suggested new classes and size
 */
export function suggestIconMigration(
  currentClasses: string,
  context?: string
): {
  suggestedSize: IconSize | null;
  suggestedClasses: string;
  warnings: string[];
} {
  const warnings: string[] = [];

  // Extract size classes from current classes
  const sizeMatch = currentClasses.match(/w-(\d+)\s+h-\1/);
  let suggestedSize: IconSize | null = null;

  if (sizeMatch) {
    const currentSize = `w-${sizeMatch[1]} h-${sizeMatch[1]}`;

    // Map common oversized icons to appropriate sizes
    const sizeMap: Record<string, IconSize> = {
      'w-3 h-3': 'xs',
      'w-4 h-4': 'sm',
      'w-5 h-5': 'md',
      'w-6 h-6': 'lg',
      'w-8 h-8': 'xl',
      'w-10 h-10': 'lg', // Reduce oversized
      'w-12 h-12': 'xl', // Reduce oversized
      'w-16 h-16': 'xl', // Reduce oversized
    };

    suggestedSize = sizeMap[currentSize] || null;

    if (!suggestedSize) {
      warnings.push(`Unknown size pattern: ${currentSize}`);
      suggestedSize = 'sm'; // Default fallback
    }

    // Context-specific suggestions
    if (context && suggestedSize) {
      const contextSize = getContextIconSize(context as any);
      if (suggestedSize !== contextSize) {
        warnings.push(`Context "${context}" typically uses "${contextSize}" but "${suggestedSize}" was suggested based on current size`);
        suggestedSize = contextSize; // Prefer context-appropriate size
      }
    }
  } else {
    warnings.push('No size classes found in current classes');
    suggestedSize = context ? getContextIconSize(context as any) : 'sm';
  }

  // Remove old size classes and add new ones
  const otherClasses = currentClasses
    .replace(/w-\d+\s+h-\d+/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  const suggestedClasses = combineIconClasses(suggestedSize, otherClasses || undefined);

  return {
    suggestedSize,
    suggestedClasses,
    warnings,
  };
}