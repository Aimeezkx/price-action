# Icon Usage Examples

This document provides practical examples of how to implement the icon sizing system across different components and contexts in the Document Learning App.

## Table of Contents

1. [Navigation Examples](#navigation-examples)
2. [Button Examples](#button-examples)
3. [Status Indicator Examples](#status-indicator-examples)
4. [Feature Card Examples](#feature-card-examples)
5. [Empty State Examples](#empty-state-examples)
6. [Loading State Examples](#loading-state-examples)
7. [Form Examples](#form-examples)
8. [Dashboard Examples](#dashboard-examples)
9. [Mobile-Specific Examples](#mobile-specific-examples)
10. [Migration Examples](#migration-examples)

## Navigation Examples

### Main Navigation Menu
```tsx
import { Home, FileText, Search, User, Settings } from 'lucide-react';
import { getContextIconProps } from '../lib/icon-component-helpers';

const MainNavigation = () => {
  const iconProps = getContextIconProps('navigation', 'text-gray-600');

  const navItems = [
    { icon: Home, label: 'Home', href: '/' },
    { icon: FileText, label: 'Documents', href: '/documents' },
    { icon: Search, label: 'Search', href: '/search' },
    { icon: User, label: 'Profile', href: '/profile' },
    { icon: Settings, label: 'Settings', href: '/settings' },
  ];

  return (
    <nav className="space-y-1">
      {navItems.map((item) => (
        <a
          key={item.href}
          href={item.href}
          className="flex items-center space-x-3 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors"
        >
          <item.icon {...iconProps} />
          <span className="text-sm font-medium">{item.label}</span>
        </a>
      ))}
    </nav>
  );
};
```

### Breadcrumb Navigation
```tsx
import { ChevronRight, Home } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const Breadcrumb = ({ items }) => {
  const homeIconProps = getIconProps('sm', 'navigation', 'text-gray-500');
  const chevronProps = getIconProps('xs', 'navigation', 'text-gray-400');

  return (
    <nav className="flex items-center space-x-2 text-sm">
      <a href="/" className="flex items-center text-gray-500 hover:text-gray-700">
        <Home {...homeIconProps} />
      </a>

      {items.map((item, index) => (
        <div key={index} className="flex items-center space-x-2">
          <ChevronRight {...chevronProps} />
          <a
            href={item.href}
            className={`${index === items.length - 1 ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
          >
            {item.label}
          </a>
        </div>
      ))}
    </nav>
  );
};
```

### Tab Navigation
```tsx
import { FileText, BarChart, Settings } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const TabNavigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'analytics', label: 'Analytics', icon: BarChart },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-8">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const iconProps = getIconProps('sm', 'navigation',
            isActive ? 'text-blue-600' : 'text-gray-500'
          );

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                isActive
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon {...iconProps} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};
```

## Button Examples

### Primary Action Buttons
```tsx
import { Download, Share, Save, Trash2 } from 'lucide-react';
import { getContextIconProps } from '../lib/icon-component-helpers';

const ActionButtons = () => {
  const primaryIconProps = getContextIconProps('primaryButton', 'text-white');
  const secondaryIconProps = getContextIconProps('button', 'text-gray-700');
  const dangerIconProps = getContextIconProps('button', 'text-red-600');

  return (
    <div className="flex space-x-3">
      {/* Primary button */}
      <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center space-x-2 transition-colors">
        <Download {...primaryIconProps} />
        <span>Download</span>
      </button>

      {/* Secondary button */}
      <button className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 flex items-center space-x-2 transition-colors">
        <Share {...secondaryIconProps} />
        <span>Share</span>
      </button>

      {/* Save button */}
      <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center space-x-2 transition-colors">
        <Save {...primaryIconProps} />
        <span>Save</span>
      </button>

      {/* Danger button */}
      <button className="bg-white border border-red-300 text-red-600 px-4 py-2 rounded-md hover:bg-red-50 flex items-center space-x-2 transition-colors">
        <Trash2 {...dangerIconProps} />
        <span>Delete</span>
      </button>
    </div>
  );
};
```

### Icon-Only Buttons
```tsx
import { Edit, Copy, ExternalLink, MoreHorizontal } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const IconButtons = () => {
  const iconProps = getIconProps('sm', 'button', 'text-gray-600');

  return (
    <div className="flex space-x-2">
      <button
        className="p-2 rounded-md hover:bg-gray-100 transition-colors"
        title="Edit"
      >
        <Edit {...iconProps} />
      </button>

      <button
        className="p-2 rounded-md hover:bg-gray-100 transition-colors"
        title="Copy"
      >
        <Copy {...iconProps} />
      </button>

      <button
        className="p-2 rounded-md hover:bg-gray-100 transition-colors"
        title="Open in new tab"
      >
        <ExternalLink {...iconProps} />
      </button>

      <button
        className="p-2 rounded-md hover:bg-gray-100 transition-colors"
        title="More options"
      >
        <MoreHorizontal {...iconProps} />
      </button>
    </div>
  );
};
```

### Floating Action Button
```tsx
import { Plus } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const FloatingActionButton = ({ onClick }) => {
  const iconProps = getIconProps('md', 'button', 'text-white');

  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      title="Add new document"
    >
      <Plus {...iconProps} />
    </button>
  );
};
```

## Status Indicator Examples

### Connection Status
```tsx
import { Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const ConnectionStatus = ({ status }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          text: 'Connected',
          iconClass: 'text-green-500',
          textClass: 'text-green-700',
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected',
          iconClass: 'text-red-500',
          textClass: 'text-red-700',
        };
      case 'unstable':
        return {
          icon: AlertTriangle,
          text: 'Unstable Connection',
          iconClass: 'text-yellow-500',
          textClass: 'text-yellow-700',
        };
      default:
        return {
          icon: WifiOff,
          text: 'Unknown',
          iconClass: 'text-gray-500',
          textClass: 'text-gray-700',
        };
    }
  };

  const config = getStatusConfig(status);
  const iconProps = getIconProps('xs', 'status', config.iconClass);

  return (
    <div className="flex items-center space-x-2">
      <config.icon {...iconProps} />
      <span className={`text-sm ${config.textClass}`}>{config.text}</span>
    </div>
  );
};
```

### Processing Status
```tsx
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const ProcessingStatus = ({ status, message }) => {
  const statusConfig = {
    success: {
      icon: CheckCircle,
      iconClass: 'text-green-500',
      bgClass: 'bg-green-50',
      borderClass: 'border-green-200',
    },
    error: {
      icon: XCircle,
      iconClass: 'text-red-500',
      bgClass: 'bg-red-50',
      borderClass: 'border-red-200',
    },
    warning: {
      icon: AlertCircle,
      iconClass: 'text-yellow-500',
      bgClass: 'bg-yellow-50',
      borderClass: 'border-yellow-200',
    },
    processing: {
      icon: Clock,
      iconClass: 'text-blue-500',
      bgClass: 'bg-blue-50',
      borderClass: 'border-blue-200',
    },
  };

  const config = statusConfig[status] || statusConfig.processing;
  const iconProps = getIconProps('sm', 'status', config.iconClass);

  return (
    <div className={`p-4 rounded-md border ${config.bgClass} ${config.borderClass}`}>
      <div className="flex items-center space-x-3">
        <config.icon {...iconProps} />
        <div>
          <p className="text-sm font-medium text-gray-900">
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </p>
          {message && (
            <p className="text-sm text-gray-600 mt-1">{message}</p>
          )}
        </div>
      </div>
    </div>
  );
};
```

## Feature Card Examples

### Homepage Feature Cards
```tsx
import { FileText, Search, BarChart, Shield } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const FeatureCards = () => {
  const features = [
    {
      icon: FileText,
      title: 'Document Processing',
      description: 'Advanced AI-powered document analysis and knowledge extraction.',
      color: 'blue',
    },
    {
      icon: Search,
      title: 'Smart Search',
      description: 'Semantic search across all your documents with intelligent filtering.',
      color: 'green',
    },
    {
      icon: BarChart,
      title: 'Analytics',
      description: 'Comprehensive insights and analytics for your document library.',
      color: 'purple',
    },
    {
      icon: Shield,
      title: 'Security',
      description: 'Enterprise-grade security with end-to-end encryption.',
      color: 'red',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {features.map((feature, index) => {
        const iconProps = getIconProps('md', 'feature', `text-${feature.color}-600`);

        return (
          <div key={index} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div className={`inline-flex p-3 rounded-lg bg-${feature.color}-100 mb-4`}>
              <feature.icon {...iconProps} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {feature.title}
            </h3>
            <p className="text-gray-600 text-sm">
              {feature.description}
            </p>
          </div>
        );
      })}
    </div>
  );
};
```

### Service Cards
```tsx
import { Upload, Download, Share2, Archive } from 'lucide-react';
import { getContextIconProps } from '../lib/icon-component-helpers';

const ServiceCards = () => {
  const services = [
    {
      icon: Upload,
      title: 'Upload Documents',
      description: 'Drag and drop or browse to upload your documents',
      action: 'Upload Now',
    },
    {
      icon: Download,
      title: 'Export Data',
      description: 'Export your processed documents in various formats',
      action: 'Export',
    },
    {
      icon: Share2,
      title: 'Share Collections',
      description: 'Share document collections with team members',
      action: 'Share',
    },
    {
      icon: Archive,
      title: 'Archive Old Files',
      description: 'Organize and archive documents you no longer need',
      action: 'Archive',
    },
  ];

  const iconProps = getContextIconProps('feature', 'text-gray-700');

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {services.map((service, index) => (
        <div key={index} className="border border-gray-200 rounded-lg p-6 hover:border-gray-300 transition-colors">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <service.icon {...iconProps} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {service.title}
              </h3>
              <p className="text-gray-600 text-sm mb-4">
                {service.description}
              </p>
              <button className="text-blue-600 text-sm font-medium hover:text-blue-700">
                {service.action} →
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

## Empty State Examples

### Document List Empty State
```tsx
import { FileText, Upload } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const DocumentsEmptyState = ({ onUpload }) => {
  const emptyIconProps = getIconProps('xl', 'empty-state', 'text-gray-400');
  const uploadIconProps = getIconProps('sm', 'button', 'text-white');

  return (
    <div className="text-center py-12">
      <FileText {...emptyIconProps} className="mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        No documents found
      </h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">
        Get started by uploading your first document. We support PDF, Word, and text files.
      </p>
      <button
        onClick={onUpload}
        className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 flex items-center space-x-2 mx-auto transition-colors"
      >
        <Upload {...uploadIconProps} />
        <span>Upload Document</span>
      </button>
    </div>
  );
};
```

### Search Results Empty State
```tsx
import { Search } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const SearchEmptyState = ({ query, onClearSearch }) => {
  const searchIconProps = getIconProps('lg', 'empty-state', 'text-gray-400');

  return (
    <div className="text-center py-16">
      <Search {...searchIconProps} className="mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        No results found
      </h3>
      <p className="text-gray-500 mb-6">
        We couldn't find any documents matching "{query}". Try adjusting your search terms.
      </p>
      <div className="space-x-4">
        <button
          onClick={onClearSearch}
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Clear search
        </button>
        <button className="text-gray-600 hover:text-gray-700 font-medium">
          Browse all documents
        </button>
      </div>
    </div>
  );
};
```

## Loading State Examples

### Page Loading
```tsx
import { Loader2 } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const PageLoading = ({ message = 'Loading...' }) => {
  const loaderProps = getIconProps('lg', 'loading', 'text-blue-600 animate-spin');

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 {...loaderProps} className="mb-4" />
      <p className="text-gray-600">{message}</p>
    </div>
  );
};
```

### Inline Loading
```tsx
import { Loader2 } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const InlineLoading = ({ text = 'Loading...' }) => {
  const loaderProps = getIconProps('sm', 'status', 'text-gray-500 animate-spin');

  return (
    <div className="flex items-center space-x-2">
      <Loader2 {...loaderProps} />
      <span className="text-sm text-gray-600">{text}</span>
    </div>
  );
};
```

### Button Loading State
```tsx
import { Loader2, Save } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const LoadingButton = ({ loading, onClick, children }) => {
  const loaderProps = getIconProps('sm', 'button', 'text-white animate-spin');
  const saveProps = getIconProps('sm', 'button', 'text-white');

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`px-4 py-2 rounded-md flex items-center space-x-2 transition-colors ${
        loading
          ? 'bg-blue-400 cursor-not-allowed'
          : 'bg-blue-600 hover:bg-blue-700'
      } text-white`}
    >
      {loading ? (
        <Loader2 {...loaderProps} />
      ) : (
        <Save {...saveProps} />
      )}
      <span>{loading ? 'Saving...' : children}</span>
    </button>
  );
};
```

## Form Examples

### Input with Icon
```tsx
import { Search, Mail, Lock } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const IconInput = ({ icon: Icon, type = 'text', placeholder, ...props }) => {
  const iconProps = getIconProps('sm', 'form', 'text-gray-400');

  return (
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Icon {...iconProps} />
      </div>
      <input
        type={type}
        className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        placeholder={placeholder}
        {...props}
      />
    </div>
  );
};

// Usage examples
const FormExamples = () => (
  <div className="space-y-4">
    <IconInput icon={Search} placeholder="Search documents..." />
    <IconInput icon={Mail} type="email" placeholder="Enter your email" />
    <IconInput icon={Lock} type="password" placeholder="Enter password" />
  </div>
);
```

### Form Validation States
```tsx
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const ValidatedInput = ({ label, error, success, warning, ...props }) => {
  const getValidationIcon = () => {
    if (error) {
      const iconProps = getIconProps('sm', 'status', 'text-red-500');
      return <XCircle {...iconProps} />;
    }
    if (success) {
      const iconProps = getIconProps('sm', 'status', 'text-green-500');
      return <CheckCircle {...iconProps} />;
    }
    if (warning) {
      const iconProps = getIconProps('sm', 'status', 'text-yellow-500');
      return <AlertCircle {...iconProps} />;
    }
    return null;
  };

  const getBorderColor = () => {
    if (error) return 'border-red-300 focus:border-red-500 focus:ring-red-500';
    if (success) return 'border-green-300 focus:border-green-500 focus:ring-green-500';
    if (warning) return 'border-yellow-300 focus:border-yellow-500 focus:ring-yellow-500';
    return 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <div className="relative">
        <input
          className={`block w-full px-3 py-2 rounded-md placeholder-gray-400 focus:outline-none focus:ring-1 ${getBorderColor()}`}
          {...props}
        />
        {(error || success || warning) && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            {getValidationIcon()}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      {success && (
        <p className="mt-1 text-sm text-green-600">{success}</p>
      )}
      {warning && (
        <p className="mt-1 text-sm text-yellow-600">{warning}</p>
      )}
    </div>
  );
};
```

## Dashboard Examples

### Metric Cards
```tsx
import { Users, FileText, TrendingUp, Clock } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const MetricCards = ({ metrics }) => {
  const iconConfigs = {
    users: { icon: Users, color: 'blue' },
    documents: { icon: FileText, color: 'green' },
    growth: { icon: TrendingUp, color: 'purple' },
    time: { icon: Clock, color: 'orange' },
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Object.entries(metrics).map(([key, value]) => {
        const config = iconConfigs[key];
        if (!config) return null;

        const iconProps = getIconProps('md', 'feature', `text-${config.color}-600`);

        return (
          <div key={key} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 capitalize">
                  {key.replace(/([A-Z])/g, ' $1').trim()}
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {typeof value === 'number' ? value.toLocaleString() : value}
                </p>
              </div>
              <div className={`p-3 rounded-full bg-${config.color}-100`}>
                <config.icon {...iconProps} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
```

### Activity Feed
```tsx
import { FileText, Upload, Download, Share } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const ActivityFeed = ({ activities }) => {
  const getActivityIcon = (type) => {
    const iconMap = {
      upload: Upload,
      download: Download,
      share: Share,
      view: FileText,
    };
    return iconMap[type] || FileText;
  };

  const getActivityColor = (type) => {
    const colorMap = {
      upload: 'text-green-600',
      download: 'text-blue-600',
      share: 'text-purple-600',
      view: 'text-gray-600',
    };
    return colorMap[type] || 'text-gray-600';
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
      </div>
      <div className="divide-y divide-gray-200">
        {activities.map((activity, index) => {
          const Icon = getActivityIcon(activity.type);
          const iconProps = getIconProps('sm', 'status', getActivityColor(activity.type));

          return (
            <div key={index} className="px-6 py-4 flex items-center space-x-3">
              <Icon {...iconProps} />
              <div className="flex-1">
                <p className="text-sm text-gray-900">{activity.description}</p>
                <p className="text-xs text-gray-500">{activity.timestamp}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

## Mobile-Specific Examples

### Mobile Navigation
```tsx
import { Home, Search, FileText, User, Menu } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const MobileNavigation = ({ isMenuOpen, toggleMenu }) => {
  const iconProps = getIconProps('sm', 'navigation', 'text-gray-600');
  const menuIconProps = getIconProps('md', 'button', 'text-gray-700');

  return (
    <>
      {/* Mobile header */}
      <div className="md:hidden bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-900">Document App</h1>
        <button onClick={toggleMenu} className="p-2">
          <Menu {...menuIconProps} />
        </button>
      </div>

      {/* Mobile bottom navigation */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="grid grid-cols-4 py-2">
          {[
            { icon: Home, label: 'Home' },
            { icon: Search, label: 'Search' },
            { icon: FileText, label: 'Documents' },
            { icon: User, label: 'Profile' },
          ].map((item, index) => (
            <button key={index} className="flex flex-col items-center py-2 px-1">
              <item.icon {...iconProps} />
              <span className="text-xs text-gray-600 mt-1">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
};
```

### Touch-Friendly Buttons
```tsx
import { Edit, Delete, Share } from 'lucide-react';
import { getIconProps } from '../lib/icon-component-helpers';

const TouchFriendlyActions = ({ onEdit, onDelete, onShare }) => {
  const iconProps = getIconProps('sm', 'button', 'text-gray-600');

  return (
    <div className="flex space-x-2">
      <button
        onClick={onEdit}
        className="p-3 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
        title="Edit"
      >
        <Edit {...iconProps} />
      </button>

      <button
        onClick={onShare}
        className="p-3 rounded-full bg-blue-100 hover:bg-blue-200 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
        title="Share"
      >
        <Share {...iconProps} />
      </button>

      <button
        onClick={onDelete}
        className="p-3 rounded-full bg-red-100 hover:bg-red-200 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
        title="Delete"
      >
        <Delete {...iconProps} />
      </button>
    </div>
  );
};
```

## Migration Examples

### Before and After Comparison
```tsx
// BEFORE: Oversized icons
const OldFeatureCard = () => (
  <div className="bg-white p-6 rounded-lg shadow">
    <div className="flex items-center space-x-4 mb-4">
      <div className="bg-blue-100 p-4 rounded-lg">
        <FileText className="w-12 h-12 text-blue-600" /> {/* Too large */}
      </div>
      <h3 className="text-lg font-semibold">Document Processing</h3>
    </div>
    <p>Advanced document analysis capabilities.</p>
  </div>
);

// AFTER: Appropriately sized icons
const NewFeatureCard = () => {
  const iconProps = getIconProps('md', 'feature', 'text-blue-600');

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center space-x-3 mb-4"> {/* Reduced spacing */}
        <div className="bg-blue-100 p-2 rounded-lg"> {/* Reduced padding */}
          <FileText {...iconProps} /> {/* Appropriately sized */}
        </div>
        <h3 className="text-lg font-semibold">Document Processing</h3>
      </div>
      <p>Advanced document analysis capabilities.</p>
    </div>
  );
};
```

### Migration Helper Usage
```tsx
import { migrateIconSize } from '../lib/icon-utils';

// Migration script example
const migrateComponent = (oldClassName) => {
  const newSize = migrateIconSize(oldClassName);
  console.log(`Migrate ${oldClassName} to size: ${newSize}`);

  // Apply new size with context
  const newProps = getIconProps(newSize, 'feature');
  return newProps;
};

// Usage
const oldClasses = ['w-12 h-12', 'w-10 h-10', 'w-8 h-8'];
oldClasses.forEach(className => {
  const newProps = migrateComponent(className);
  console.log(`New classes: ${newProps.className}`);
});
```

---

These examples demonstrate the practical implementation of the icon sizing system across various components and contexts. Use them as reference when implementing or migrating icons in your components.