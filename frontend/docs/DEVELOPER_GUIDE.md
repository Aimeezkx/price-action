# Developer Guide: Icon Sizing System

## Quick Start

### 1. Installation
The icon sizing system is already integrated into the project. No additional installation required.

### 2. Basic Usage
```tsx
import { Home, Search, FileText } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

// Simple usage with size
const iconProps = getIconProps('sm', 'navigation');
<Home {...iconProps} />

// With additional classes
const styledProps = getIconProps('md', 'button', 'text-blue-500 hover:text-blue-600');
<Search {...styledProps} />
```

### 3. Context-Based Usage
```tsx
import { getContextIconProps } from '../lib/icon-component-helpers';

// Automatically get the right size for context
const navProps = getContextIconProps('navigation');
const buttonProps = getContextIconProps('primaryButton');
const statusProps = getContextIconProps('status');
```

## API Reference

### Core Functions

#### `getIconProps(size, context?, additionalClasses?)`
Returns props object with appropriate className for direct spreading onto icon components.

**Parameters:**
- `size`: `'xs' | 'sm' | 'md' | 'lg' | 'xl'`
- `context`: `'navigation' | 'button' | 'status' | 'feature' | 'empty-state'` (optional)
- `additionalClasses`: `string` (optional)

**Returns:** `{ className: string }`

```tsx
const props = getIconProps('sm', 'navigation', 'text-gray-600');
// Returns: { className: 'w-4 h-4 text-gray-600' }
```

#### `getContextIconProps(context, additionalClasses?)`
Returns props object with size automatically determined by context.

**Parameters:**
- `context`: `'navigation' | 'button' | 'primaryButton' | 'status' | 'feature' | 'emptyState' | 'emptyStateLarge'`
- `additionalClasses`: `string` (optional)

**Returns:** `{ className: string }`

```tsx
const props = getContextIconProps('navigation', 'text-gray-600');
// Returns: { className: 'w-4 h-4 text-gray-600' }
```

#### `createIconClass(size, additionalClasses?)`
Returns className string for direct application.

**Parameters:**
- `size`: `'xs' | 'sm' | 'md' | 'lg' | 'xl'`
- `additionalClasses`: `string` (optional)

**Returns:** `string`

```tsx
const className = createIconClass('md', 'text-blue-500');
// Returns: 'w-5 h-5 text-blue-500'
```

### Utility Functions

#### `getIconSizeClass(size)`
Returns Tailwind CSS classes for a given size.

```tsx
const sizeClass = getIconSizeClass('md');
// Returns: 'w-5 h-5'
```

#### `getContextIconSize(context)`
Returns recommended size for a given context.

```tsx
const size = getContextIconSize('navigation');
// Returns: 'sm'
```

#### `validateIconSize(size, context)`
Validates if a size is appropriate for a context (development only).

```tsx
const isValid = validateIconSize('xl', 'navigation');
// Returns: false (and logs warning in development)
```

#### `migrateIconSize(oldClassName)`
Suggests new size based on old Tailwind classes.

```tsx
const newSize = migrateIconSize('w-12 h-12');
// Returns: 'xl'
```

## Implementation Patterns

### Component Integration

#### Method 1: Direct Props Spreading
```tsx
import { getIconProps } from '../lib/icon-component-helpers';

const NavigationItem = ({ icon: Icon, label }) => {
  const iconProps = getIconProps('sm', 'navigation', 'text-gray-600');

  return (
    <div className="flex items-center space-x-2">
      <Icon {...iconProps} />
      <span>{label}</span>
    </div>
  );
};
```

#### Method 2: Context-Based Sizing
```tsx
import { getContextIconProps } from '../lib/icon-component-helpers';

const ActionButton = ({ icon: Icon, children, primary = false }) => {
  const iconProps = getContextIconProps(
    primary ? 'primaryButton' : 'button',
    'mr-2'
  );

  return (
    <button className={`px-4 py-2 rounded ${primary ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}>
      <Icon {...iconProps} />
      {children}
    </button>
  );
};
```

#### Method 3: Custom Hook
```tsx
import { useMemo } from 'react';
import { getContextIconProps } from '../lib/icon-component-helpers';

const useIconProps = (context, additionalClasses = '') => {
  return useMemo(() =>
    getContextIconProps(context, additionalClasses),
    [context, additionalClasses]
  );
};

const MyComponent = () => {
  const navIconProps = useIconProps('navigation', 'text-gray-600');

  return <Home {...navIconProps} />;
};
```

### Reusable Components

#### Icon Wrapper Component
```tsx
import { ReactElement, cloneElement } from 'react';
import { getIconProps } from '../lib/icon-component-helpers';

interface IconWrapperProps {
  icon: ReactElement;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  context?: string;
  className?: string;
}

const IconWrapper = ({ icon, size = 'sm', context, className = '' }: IconWrapperProps) => {
  const iconProps = getIconProps(size, context, className);
  return cloneElement(icon, iconProps);
};

// Usage
<IconWrapper icon={<Home />} size="sm" context="navigation" className="text-gray-600" />
```

#### Contextual Icon Components
```tsx
import { ComponentType } from 'react';
import { getContextIconProps } from '../lib/icon-component-helpers';

const NavIcon = ({ icon: Icon, className = '' }: { icon: ComponentType, className?: string }) => {
  const props = getContextIconProps('navigation', className);
  return <Icon {...props} />;
};

const ButtonIcon = ({ icon: Icon, primary = false, className = '' }) => {
  const context = primary ? 'primaryButton' : 'button';
  const props = getContextIconProps(context, className);
  return <Icon {...props} />;
};

const StatusIcon = ({ icon: Icon, className = '' }) => {
  const props = getContextIconProps('status', className);
  return <Icon {...props} />;
};

// Usage
<NavIcon icon={Home} className="text-gray-600" />
<ButtonIcon icon={Save} primary className="text-white" />
<StatusIcon icon={CheckCircle} className="text-green-500" />
```

## Migration Guide

### Step 1: Identify Current Usage
Use the migration helper to identify oversized icons:

```tsx
import { migrateIconSize } from '../lib/icon-utils';

// Find current usage
const currentClasses = 'w-12 h-12 text-blue-500';
const suggestedSize = migrateIconSize(currentClasses);
console.log(`Suggested size: ${suggestedSize}`); // 'xl'
```

### Step 2: Apply Context-Appropriate Sizes
Replace with context-appropriate sizes:

```tsx
// Before
<FileText className="w-12 h-12 text-blue-500" />

// After - consider context
<FileText className="w-6 h-6 text-blue-500" /> // For feature cards
<FileText className="w-8 h-8 text-blue-500" /> // For empty states
```

### Step 3: Use Utility Functions
Replace direct classes with utility functions:

```tsx
// Before
<Home className="w-8 h-8 text-gray-600" />

// After
const iconProps = getIconProps('sm', 'navigation', 'text-gray-600');
<Home {...iconProps} />
```

### Step 4: Update Container Spacing
Adjust surrounding elements when icon sizes change:

```tsx
// Before
<div className="flex items-center space-x-4 p-4">
  <FileText className="w-12 h-12" />
  <span>Document</span>
</div>

// After
<div className="flex items-center space-x-3 p-3">
  <FileText className="w-6 h-6" />
  <span>Document</span>
</div>
```

## Testing

### Unit Testing
```tsx
import { getIconProps, getContextIconProps } from '../lib/icon-component-helpers';

describe('Icon sizing utilities', () => {
  test('getIconProps returns correct classes', () => {
    const props = getIconProps('sm', 'navigation', 'text-gray-600');
    expect(props.className).toBe('w-4 h-4 text-gray-600');
  });

  test('getContextIconProps uses appropriate size for context', () => {
    const props = getContextIconProps('navigation');
    expect(props.className).toContain('w-4 h-4');
  });
});
```

### Component Testing
```tsx
import { render } from '@testing-library/react';
import { Home } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

test('icon renders with correct size classes', () => {
  const iconProps = getIconProps('sm', 'navigation');
  const { container } = render(<Home {...iconProps} />);

  const icon = container.querySelector('svg');
  expect(icon).toHaveClass('w-4', 'h-4');
});
```

### Visual Regression Testing
```tsx
// e2e/icon-visual-regression.spec.ts
import { test, expect } from '@playwright/test';

test('navigation icons maintain consistent sizing', async ({ page }) => {
  await page.goto('/');

  // Take screenshot of navigation
  const nav = page.locator('nav');
  await expect(nav).toHaveScreenshot('navigation-icons.png');
});
```

## Best Practices

### 1. Consistency First
Always use the same size for similar elements:

```tsx
// ✅ Consistent navigation icons
const navItems = [
  { icon: Home, label: 'Home' },
  { icon: Search, label: 'Search' },
  { icon: Settings, label: 'Settings' },
];

navItems.map(item => (
  <NavIcon key={item.label} icon={item.icon} />
));
```

### 2. Context Awareness
Choose sizes based on element importance:

```tsx
// ✅ Context-appropriate sizing
<PrimaryButton icon={Download} size="md">Download</PrimaryButton>
<SecondaryButton icon={Share} size="sm">Share</SecondaryButton>
<StatusIndicator icon={CheckCircle} size="xs" />
```

### 3. Performance Considerations
Use utility functions to avoid repeated calculations:

```tsx
// ✅ Memoized icon props
const navIconProps = useMemo(() =>
  getContextIconProps('navigation', 'text-gray-600'),
  []
);

// ❌ Recalculated on every render
const iconProps = getContextIconProps('navigation', 'text-gray-600');
```

### 4. Accessibility
Ensure adequate touch targets:

```tsx
// ✅ Adequate touch target
<button className="p-3 min-w-[44px] min-h-[44px]">
  <Settings className="w-4 h-4" />
</button>

// ❌ Touch target too small
<button className="p-1">
  <Settings className="w-4 h-4" />
</button>
```

## Troubleshooting

### Common Issues

**Issue: Icons appear blurry or pixelated**
- Ensure you're using standard sizes (xs, sm, md, lg, xl)
- Avoid custom sizes that don't align with the design system
- Check if the icon library supports the target size

**Issue: Icons don't align with text**
- Use flexbox with `items-center` for proper alignment
- Check line-height compatibility
- Ensure consistent spacing utilities

**Issue: Development warnings about inappropriate sizes**
- Review the context guidelines in the style guide
- Use `getContextIconProps` for automatic size selection
- Consider if the element truly needs a larger icon

**Issue: Icons too small on mobile devices**
- Test on actual devices, not just browser dev tools
- Consider larger touch targets for interactive elements
- Use responsive sizing if needed

### Debug Mode

Enable debug mode to see size recommendations:

```tsx
// Set in development environment
localStorage.setItem('icon-debug', 'true');

// Will log recommendations to console
const props = getIconProps('xl', 'navigation'); // Logs warning
```

### Performance Monitoring

Monitor icon rendering performance:

```tsx
import { performance } from 'perf_hooks';

const start = performance.now();
const props = getIconProps('sm', 'navigation');
const end = performance.now();

console.log(`Icon props generation took ${end - start} milliseconds`);
```

## Advanced Usage

### Dynamic Sizing
```tsx
const DynamicIcon = ({ importance, icon: Icon }) => {
  const size = importance === 'high' ? 'lg' :
               importance === 'medium' ? 'md' : 'sm';

  const props = getIconProps(size, 'feature');
  return <Icon {...props} />;
};
```

### Responsive Icons
```tsx
const ResponsiveIcon = ({ icon: Icon }) => {
  const mobileProps = getIconProps('sm', 'navigation', 'md:hidden');
  const desktopProps = getIconProps('md', 'navigation', 'hidden md:block');

  return (
    <>
      <Icon {...mobileProps} />
      <Icon {...desktopProps} />
    </>
  );
};
```

### Theme Integration
```tsx
const ThemedIcon = ({ icon: Icon, theme = 'light' }) => {
  const themeClasses = theme === 'dark' ? 'text-white' : 'text-gray-600';
  const props = getIconProps('sm', 'navigation', themeClasses);

  return <Icon {...props} />;
};
```

---

For more detailed information, see the [Icon Style Guide](./ICON_STYLE_GUIDE.md).