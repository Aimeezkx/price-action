import React from 'react';
import { PrivacySettings } from '../components/PrivacySettings';

export function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="py-8">
        <PrivacySettings />
      </div>
    </div>
  );
}

export default PrivacyPage;