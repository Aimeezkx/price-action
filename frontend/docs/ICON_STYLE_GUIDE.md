# Icon Style Guide

## Overview

This style guide establishes the standardized icon sizing system for the Document Learning App frontend. The system is designed to create visual consistency, improve user experience, and maintain a clean, professional interface based on v3 UI design principles.

## Quick Reference

| Size | Class | Pixels | Context | Example Use Cases |
|------|-------|--------|---------|-------------------|
| `xs` | `w-3 h-3` | 12px | Inline indicators | Status dots, badges, inline icons |
| `sm` | `w-4 h-4` | 16px | Navigation & buttons | Menu items, form buttons, toolbar icons |
| `md` | `w-5 h-5` | 20px | Primary actions | Important buttons, feature highlights |
| `lg` | `w-6 h-6` | 24px | Section headers | Feature cards, section icons |
| `xl` | `w-8 h-8` | 32px | Empty states | Placeholder content, major status indicators |

## Design Principles

### 1. Visual Hierarchy
Icons should support, not dominate, the content hierarchy:
- **Smaller icons** for supporting elements (navigation, status)
- **Medium icons** for primary actions and features
- **Larger icons** only for empty states and major visual elements

### 2. Context Appropriateness
Icon size should match the semantic importance of the element:
- Navigation icons remain small to avoid overwhelming the interface
- Action buttons use medium sizes to indicate interactivity
- Empty states use larger icons to fill space appropriately

### 3. Consistency
Similar elements should use the same icon sizes across the application:
- All navigation items use `sm` (w-4 h-4)
- All primary buttons use `md` (w-5 h-5)
- All status indicators use `xs` or `sm` depending on importance

## Context-Based Guidelines

### Navigation Icons
**Recommended Size:** `sm` (w-4 h-4)

```tsx
// ✅ Correct
<Home className="w-4 h-4" />

// ❌ Avoid - too large for navigation
<Home className="w-8 h-8" />
```

**Use Cases:**
- Main navigation menu items
- Breadcrumb navigation
- Tab navigation
- Sidebar menu items

### Button Icons
**Recommended Sizes:**
- Regular buttons: `sm` (w-4 h-4)
- Primary buttons: `md` (w-5 h-5)
- Large action buttons: `lg` (w-6 h-6)

```tsx
// ✅ Regular button
<button className="flex items-center space-x-2">
  <Save className="w-4 h-4" />
  <span>Save</span>
</button>

// ✅ Primary button
<button className="bg-blue-500 text-white flex items-center space-x-2">
  <Download className="w-5 h-5" />
  <span>Download</span>
</button>

// ❌ Avoid - oversized for button
<button className="flex items-center space-x-2">
  <Save className="w-12 h-12" />
  <span>Save</span>
</button>
```

### Status Indicators
**Recommended Sizes:**
- Inline status: `xs` (w-3 h-3)
- Important status: `sm` (w-4 h-4)

```tsx
// ✅ Inline status
<div className="flex items-center space-x-1">
  <Circle className="w-3 h-3 text-green-500" />
  <span className="text-sm">Online</span>
</div>

// ✅ Important status
<div className="flex items-center space-x-2">
  <AlertTriangle className="w-4 h-4 text-yellow-500" />
  <span>Warning: Check connection</span>
</div>
```

### Feature Cards
**Recommended Sizes:**
- Standard features: `md` (w-5 h-5)
- Highlighted features: `lg` (w-6 h-6)

```tsx
// ✅ Feature card
<div className="bg-white p-6 rounded-lg">
  <div className="flex items-center space-x-3 mb-4">
    <div className="bg-blue-100 p-2 rounded-lg">
      <FileText className="w-5 h-5 text-blue-600" />
    </div>
    <h3 className="text-lg font-semibold">Document Processing</h3>
  </div>
  <p>Advanced document analysis capabilities.</p>
</div>
```

### Empty States
**Recommended Sizes:**
- Compact empty states: `lg` (w-6 h-6)
- Prominent empty states: `xl` (w-8 h-8)

```tsx
// ✅ Empty state
<div className="text-center py-12">
  <FileX className="w-8 h-8 text-gray-400 mx-auto mb-4" />
  <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
  <p className="text-gray-500">Upload your first document to get started.</p>
</div>
```

### Loading States
**Recommended Sizes:**
- Inline loading: `sm` (w-4 h-4)
- Page loading: `md` (w-5 h-5) to `lg` (w-6 h-6)

```tsx
// ✅ Inline loading
<div className="flex items-center space-x-2">
  <Loader2 className="w-4 h-4 animate-spin" />
  <span>Loading...</span>
</div>

// ✅ Page loading
<div className="text-center py-8">
  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
  <p>Processing document...</p>
</div>
```

## Implementation Guidelines

### Using the Icon Utility System

The application provides utility functions to ensure consistent icon sizing:

```tsx
import { getIconProps, getContextIconProps, createIconClass } from '../lib/icon-component-helpers';

// Method 1: Direct size specification
const iconProps = getIconProps('sm', 'navigation', 'text-gray-600');
<Home {...iconProps} />

// Method 2: Context-based sizing
const buttonProps = getContextIconProps('button', 'text-white');
<Save {...buttonProps} />

// Method 3: Class generation
const iconClass = createIconClass('md', 'text-blue-500');
<Download className={iconClass} />
```

### Migration from Oversized Icons

When updating existing icons, follow this migration pattern:

```tsx
// Before (oversized)
<FileText className="w-12 h-12 text-blue-500" />

// After (appropriately sized)
<FileText className="w-6 h-6 text-blue-500" />

// Or using utilities
const iconProps = getIconProps('lg', 'feature', 'text-blue-500');
<FileText {...iconProps} />
```

### Common Migration Mappings

| Old Size | New Size | Context |
|----------|----------|---------|
| `w-12 h-12` | `w-6 h-6` or `w-8 h-8` | Feature cards, empty states |
| `w-10 h-10` | `w-6 h-6` | Feature highlights |
| `w-8 h-8` | `w-5 h-5` or `w-6 h-6` | Most contexts |
| `w-6 h-6` | `w-4 h-4` or `w-5 h-5` | Navigation, buttons |

## Accessibility Considerations

### Touch Targets
Ensure clickable icons meet minimum accessibility requirements:

```tsx
// ✅ Adequate touch target
<button className="p-3"> {/* 48px minimum touch target */}
  <Settings className="w-4 h-4" />
</button>

// ❌ Touch target too small
<button className="p-1">
  <Settings className="w-4 h-4" />
</button>
```

### Visual Hierarchy
Icons should support, not interfere with, screen reader navigation:
- Use appropriate ARIA labels
- Ensure sufficient color contrast
- Maintain logical tab order

## Testing Guidelines

### Visual Regression Testing
Test icon changes across different contexts:

```bash
# Run icon-specific tests
npm test icon-utils
npm test icon-component-helpers

# Run visual regression tests
npm run test:e2e -- icon-visual-regression.spec.ts
```

### Responsive Testing
Verify icon appearance across screen sizes:

```bash
# Test responsive behavior
npm run test:e2e -- icon-responsive-behavior.spec.ts
```

### Accessibility Testing
Ensure icons meet accessibility standards:

```bash
# Run accessibility tests
npm run test:a11y
```

## Development Workflow

### 1. Planning Phase
- Identify the context (navigation, button, status, etc.)
- Choose appropriate size based on context guidelines
- Consider surrounding elements and spacing

### 2. Implementation Phase
- Use utility functions for consistency
- Apply appropriate CSS classes
- Test visual impact

### 3. Review Phase
- Verify size appropriateness
- Check accessibility compliance
- Test across different screen sizes

### 4. Documentation Phase
- Update component documentation
- Add usage examples if introducing new patterns

## Common Patterns

### Navigation Menu
```tsx
const NavigationMenu = () => {
  const navItems = [
    { icon: Home, label: 'Home' },
    { icon: FileText, label: 'Documents' },
    { icon: Search, label: 'Search' },
  ];

  return (
    <nav className="space-y-1">
      {navItems.map((item) => (
        <a key={item.label} className="flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-gray-100">
          <item.icon className="w-4 h-4 text-gray-600" />
          <span>{item.label}</span>
        </a>
      ))}
    </nav>
  );
};
```

### Action Button Group
```tsx
const ActionButtons = () => (
  <div className="flex space-x-2">
    <button className="bg-blue-500 text-white px-4 py-2 rounded flex items-center space-x-2">
      <Download className="w-4 h-4" />
      <span>Download</span>
    </button>
    <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded flex items-center space-x-2">
      <Share className="w-4 h-4" />
      <span>Share</span>
    </button>
  </div>
);
```

### Status Indicator List
```tsx
const StatusList = () => (
  <div className="space-y-2">
    <div className="flex items-center space-x-2">
      <CheckCircle className="w-3 h-3 text-green-500" />
      <span className="text-sm">Processing complete</span>
    </div>
    <div className="flex items-center space-x-2">
      <AlertTriangle className="w-4 h-4 text-yellow-500" />
      <span className="text-sm">Warning: Large file detected</span>
    </div>
  </div>
);
```

## Troubleshooting

### Common Issues

**Icons appear too small or too large**
- Check if you're using the appropriate size for the context
- Verify container spacing and padding
- Consider the visual hierarchy of surrounding elements

**Inconsistent icon sizes across similar elements**
- Use the utility functions to ensure consistency
- Create reusable components for common patterns
- Establish team conventions for specific use cases

**Icons don't align properly with text**
- Ensure proper flexbox alignment (`items-center`)
- Check line-height and font-size compatibility
- Use consistent spacing utilities

**Touch targets too small on mobile**
- Ensure clickable icons have adequate padding
- Test on actual devices, not just browser dev tools
- Consider larger touch targets for primary actions

### Development Warnings

The system provides helpful warnings in development mode:

```tsx
// This will warn about inappropriate size usage
<Home className="w-12 h-12" /> // Warning: Consider using smaller size for navigation
```

Enable development warnings by setting:
```bash
NODE_ENV=development
```

## Resources

### Related Files
- `src/lib/icon-utils.ts` - Core utility functions
- `src/lib/icon-component-helpers.ts` - Component integration helpers
- `src/lib/icon-usage-examples.tsx` - Practical usage examples
- `src/lib/icon-sizing-guide.md` - Technical implementation guide

### Design References
- [Tailwind CSS Sizing](https://tailwindcss.com/docs/width)
- [Lucide React Icons](https://lucide.dev/)
- [Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html)

### Testing Resources
- `src/lib/__tests__/icon-utils.test.ts` - Unit tests
- `e2e/icon-visual-regression.spec.ts` - Visual regression tests
- `e2e/icon-responsive-behavior.spec.ts` - Responsive behavior tests

## Changelog

### Version 1.0.0 (Current)
- Initial icon sizing system implementation
- Context-based size recommendations
- Utility functions for consistent usage
- Migration guidelines for existing icons
- Comprehensive testing suite

---

For questions or suggestions about the icon sizing system, please refer to the development team or create an issue in the project repository.