/**
 * Icon Usage Examples
 *
 * This file demonstrates how to use the icon sizing system with various icon libraries
 * and components. These examples can be used as reference for implementing the system
 * across the application.
 */

import { Home, Search, User, FileText, AlertCircle, CheckCircle, Download, Settings } from 'lucide-react';
import { getIconProps, getContextIconProps, createIconClass } from './icon-component-helpers';

// Example 1: Using getIconProps for direct icon sizing
export const NavigationIconExample = () => {
  const iconProps = getIconProps('sm', 'navigation', 'text-gray-600');

  return (
    <div className="flex items-center space-x-2">
      <Home {...iconProps} />
      <span>Home</span>
    </div>
  );
};

// Example 2: Using getContextIconProps for context-based sizing
export const ButtonIconExample = () => {
  const primaryButtonProps = getContextIconProps('primaryButton', 'text-white');
  const regularButtonProps = getContextIconProps('button', 'text-gray-700');

  return (
    <div className="space-x-4">
      <button className="bg-blue-500 text-white px-4 py-2 rounded flex items-center space-x-2">
        <Download {...primaryButtonProps} />
        <span>Download</span>
      </button>

      <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded flex items-center space-x-2">
        <Settings {...regularButtonProps} />
        <span>Settings</span>
      </button>
    </div>
  );
};

// Example 3: Using createIconClass for direct class application
export const StatusIndicatorExample = () => {
  const successIconClass = createIconClass('xs', 'text-green-500');
  const errorIconClass = createIconClass('sm', 'text-red-500');

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        <CheckCircle className={successIconClass} />
        <span className="text-sm text-green-700">Success</span>
      </div>

      <div className="flex items-center space-x-2">
        <AlertCircle className={errorIconClass} />
        <span className="text-sm text-red-700">Error occurred</span>
      </div>
    </div>
  );
};

// Example 4: Feature card with appropriately sized icons
export const FeatureCardExample = () => {
  const featureIconProps = getContextIconProps('feature', 'text-blue-500');

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center space-x-3 mb-4">
        <div className="bg-blue-100 p-2 rounded-lg">
          <FileText {...featureIconProps} />
        </div>
        <h3 className="text-lg font-semibold">Document Processing</h3>
      </div>
      <p className="text-gray-600">
        Advanced document analysis and knowledge extraction capabilities.
      </p>
    </div>
  );
};

// Example 5: Empty state with large icon
export const EmptyStateExample = () => {
  const emptyStateProps = getContextIconProps('emptyStateLarge', 'text-gray-400');

  return (
    <div className="text-center py-12">
      <div className="flex justify-center mb-4">
        <FileText {...emptyStateProps} />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
      <p className="text-gray-500">Get started by uploading your first document.</p>
    </div>
  );
};

// Example 6: Navigation menu with consistent icon sizing
export const NavigationMenuExample = () => {
  const navIconProps = getContextIconProps('navigation', 'text-gray-600');

  const menuItems = [
    { icon: Home, label: 'Home', href: '/' },
    { icon: FileText, label: 'Documents', href: '/documents' },
    { icon: Search, label: 'Search', href: '/search' },
    { icon: User, label: 'Profile', href: '/profile' },
  ];

  return (
    <nav className="space-y-1">
      {menuItems.map((item) => (
        <a
          key={item.href}
          href={item.href}
          className="flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-gray-100"
        >
          <item.icon {...navIconProps} />
          <span>{item.label}</span>
        </a>
      ))}
    </nav>
  );
};

// Example 7: Loading states with context-appropriate sizes
export const LoadingStateExample = () => {
  const smallLoadingClass = createIconClass('sm', 'animate-spin text-gray-500');
  const largeLoadingClass = createIconClass('md', 'animate-spin text-blue-500');

  return (
    <div className="space-y-4">
      {/* Inline loading */}
      <div className="flex items-center space-x-2">
        <div className={smallLoadingClass}>
          <div className="border-2 border-current border-t-transparent rounded-full w-full h-full animate-spin" />
        </div>
        <span className="text-sm">Loading...</span>
      </div>

      {/* Page loading */}
      <div className="text-center py-8">
        <div className={`${largeLoadingClass} mx-auto mb-2`}>
          <div className="border-2 border-current border-t-transparent rounded-full w-full h-full animate-spin" />
        </div>
        <p className="text-gray-600">Processing document...</p>
      </div>
    </div>
  );
};

// Example 8: Migration helper usage
export const MigrationExample = () => {
  // This would typically be used in a migration script or during refactoring

  // Old way (oversized icons)
  const oldClasses = 'w-12 h-12 text-blue-500 hover:text-blue-600';

  // New way using the sizing system
  const newIconProps = getIconProps('lg', 'feature', 'text-blue-500 hover:text-blue-600');

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600">
        Old classes: <code className="bg-gray-100 px-1 rounded">{oldClasses}</code>
      </div>
      <div className="text-sm text-gray-600">
        New classes: <code className="bg-gray-100 px-1 rounded">{newIconProps.className}</code>
      </div>

      <div className="flex items-center space-x-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">Old (oversized)</p>
          <FileText className={oldClasses} />
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">New (standardized)</p>
          <FileText {...newIconProps} />
        </div>
      </div>
    </div>
  );
};

// Example 9: Responsive icon usage
export const ResponsiveIconExample = () => {
  // Icons that adapt to screen size while maintaining appropriate proportions
  const mobileIconProps = getIconProps('sm', 'navigation', 'text-gray-600 md:hidden');
  const desktopIconProps = getIconProps('md', 'navigation', 'text-gray-600 hidden md:block');

  return (
    <div className="flex items-center space-x-2">
      <Home {...mobileIconProps} />
      <Home {...desktopIconProps} />
      <span>Responsive Icon</span>
    </div>
  );
};

// Example 10: Icon with validation warnings (development only)
export const ValidationExample = () => {
  // This will show warnings in development mode
  const inappropriateProps = getIconProps('xl', 'navigation', 'text-gray-600');
  const appropriateProps = getIconProps('sm', 'navigation', 'text-gray-600');

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        <Home {...inappropriateProps} />
        <span className="text-sm text-red-600">Inappropriate size (check console)</span>
      </div>
      <div className="flex items-center space-x-2">
        <Home {...appropriateProps} />
        <span className="text-sm text-green-600">Appropriate size</span>
      </div>
    </div>
  );
};