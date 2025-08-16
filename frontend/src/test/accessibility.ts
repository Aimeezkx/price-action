import { axe, toHaveNoViolations } from 'jest-axe';
import { expect } from 'vitest';

// Extend expect with jest-axe matchers
expect.extend(toHaveNoViolations);

/**
 * Test accessibility of a rendered component
 */
export const testAccessibility = async (container: HTMLElement) => {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
  return results;
};

/**
 * Test accessibility with custom rules
 */
export const testAccessibilityWithRules = async (
  container: HTMLElement,
  rules: Record<string, { enabled: boolean }>
) => {
  const results = await axe(container, {
    rules,
  });
  expect(results).toHaveNoViolations();
  return results;
};

/**
 * Test keyboard navigation
 */
export const testKeyboardNavigation = (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const results = {
    totalFocusableElements: focusableElements.length,
    elementsWithTabIndex: Array.from(focusableElements).filter(el => 
      el.hasAttribute('tabindex')
    ).length,
    elementsWithAriaLabels: Array.from(focusableElements).filter(el => 
      el.hasAttribute('aria-label') || el.hasAttribute('aria-labelledby')
    ).length,
  };

  return results;
};

/**
 * Test color contrast
 */
export const testColorContrast = async (container: HTMLElement) => {
  const results = await axe(container, {
    rules: {
      'color-contrast': { enabled: true },
    },
  });
  
  const colorContrastViolations = results.violations.filter(
    violation => violation.id === 'color-contrast'
  );

  return {
    hasColorContrastIssues: colorContrastViolations.length > 0,
    violations: colorContrastViolations,
  };
};

/**
 * Test ARIA attributes
 */
export const testAriaAttributes = (container: HTMLElement) => {
  const elementsWithAria = container.querySelectorAll('[aria-*]');
  const elementsWithRole = container.querySelectorAll('[role]');
  const elementsWithAriaLabel = container.querySelectorAll('[aria-label]');
  const elementsWithAriaLabelledBy = container.querySelectorAll('[aria-labelledby]');
  const elementsWithAriaDescribedBy = container.querySelectorAll('[aria-describedby]');

  return {
    totalAriaElements: elementsWithAria.length,
    elementsWithRole: elementsWithRole.length,
    elementsWithAriaLabel: elementsWithAriaLabel.length,
    elementsWithAriaLabelledBy: elementsWithAriaLabelledBy.length,
    elementsWithAriaDescribedBy: elementsWithAriaDescribedBy.length,
  };
};

/**
 * Test semantic HTML structure
 */
export const testSemanticStructure = (container: HTMLElement) => {
  const semanticElements = {
    headings: container.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
    landmarks: container.querySelectorAll('main, nav, aside, section, article, header, footer').length,
    lists: container.querySelectorAll('ul, ol, dl').length,
    buttons: container.querySelectorAll('button').length,
    links: container.querySelectorAll('a[href]').length,
    forms: container.querySelectorAll('form').length,
    inputs: container.querySelectorAll('input, textarea, select').length,
  };

  return semanticElements;
};

/**
 * Test screen reader compatibility
 */
export const testScreenReaderCompatibility = async (container: HTMLElement) => {
  const results = await axe(container, {
    tags: ['wcag2a', 'wcag2aa', 'section508'],
  });

  const screenReaderIssues = results.violations.filter(violation =>
    ['label', 'aria-label', 'aria-labelledby', 'aria-describedby'].some(tag =>
      violation.tags.includes(tag)
    )
  );

  return {
    hasScreenReaderIssues: screenReaderIssues.length > 0,
    violations: screenReaderIssues,
    totalViolations: results.violations.length,
  };
};

/**
 * Test focus management
 */
export const testFocusManagement = (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );

  const focusTraps = container.querySelectorAll('[data-focus-trap]');
  const skipLinks = container.querySelectorAll('[data-skip-link]');

  return {
    focusableElementsCount: focusableElements.length,
    hasFocusTraps: focusTraps.length > 0,
    hasSkipLinks: skipLinks.length > 0,
    firstFocusableElement: focusableElements[0] || null,
    lastFocusableElement: focusableElements[focusableElements.length - 1] || null,
  };
};

/**
 * Test responsive design accessibility
 */
export const testResponsiveAccessibility = async (container: HTMLElement) => {
  // Test at different viewport sizes
  const viewports = [
    { width: 320, height: 568 }, // Mobile
    { width: 768, height: 1024 }, // Tablet
    { width: 1024, height: 768 }, // Desktop
  ];

  const results = [];

  for (const viewport of viewports) {
    // Mock viewport size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: viewport.width,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: viewport.height,
    });

    // Trigger resize event
    window.dispatchEvent(new Event('resize'));

    const accessibilityResults = await axe(container);
    
    results.push({
      viewport,
      violations: accessibilityResults.violations,
      passes: accessibilityResults.passes.length,
    });
  }

  return results;
};

/**
 * Comprehensive accessibility test suite
 */
export const runAccessibilityTestSuite = async (container: HTMLElement) => {
  const results = {
    basicAccessibility: await testAccessibility(container),
    keyboardNavigation: testKeyboardNavigation(container),
    colorContrast: await testColorContrast(container),
    ariaAttributes: testAriaAttributes(container),
    semanticStructure: testSemanticStructure(container),
    screenReaderCompatibility: await testScreenReaderCompatibility(container),
    focusManagement: testFocusManagement(container),
    responsiveAccessibility: await testResponsiveAccessibility(container),
  };

  return results;
};

/**
 * Custom accessibility matchers for testing
 */
export const accessibilityMatchers = {
  toBeAccessible: async (container: HTMLElement) => {
    try {
      await testAccessibility(container);
      return {
        message: () => 'Element is accessible',
        pass: true,
      };
    } catch (error) {
      return {
        message: () => `Element has accessibility violations: ${error}`,
        pass: false,
      };
    }
  },

  toHaveKeyboardNavigation: (container: HTMLElement) => {
    const { totalFocusableElements } = testKeyboardNavigation(container);
    const pass = totalFocusableElements > 0;

    return {
      message: () => 
        pass 
          ? `Element has ${totalFocusableElements} focusable elements`
          : 'Element has no focusable elements for keyboard navigation',
      pass,
    };
  },

  toHaveSemanticStructure: (container: HTMLElement) => {
    const structure = testSemanticStructure(container);
    const hasSemanticElements = Object.values(structure).some(count => count > 0);

    return {
      message: () =>
        hasSemanticElements
          ? 'Element has semantic HTML structure'
          : 'Element lacks semantic HTML structure',
      pass: hasSemanticElements,
    };
  },
};

// Extend expect with custom matchers
declare global {
  namespace Vi {
    interface AsymmetricMatchersContaining {
      toBeAccessible(): any;
      toHaveKeyboardNavigation(): any;
      toHaveSemanticStructure(): any;
    }
  }
}

// Export types for TypeScript support
export type AccessibilityTestResults = Awaited<ReturnType<typeof runAccessibilityTestSuite>>;
export type KeyboardNavigationResults = ReturnType<typeof testKeyboardNavigation>;
export type SemanticStructureResults = ReturnType<typeof testSemanticStructure>;
export type FocusManagementResults = ReturnType<typeof testFocusManagement>;