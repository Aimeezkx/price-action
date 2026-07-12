import React from 'react';
import { PrivacySettings } from '../components/PrivacySettings';

export function PrivacyPage() {
  return (
    <div className="min-h-screen">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="sm:flex sm:items-center">
            <div className="sm:flex-auto">
              <h1 className="text-3xl font-bold text-gray-900">Privacy Settings</h1>
              <p className="mt-2 text-lg text-gray-600">
                Manage your privacy preferences and data handling
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <PrivacySettings />
      </div>
    </div>
  );
}

export default PrivacyPage;