import React from 'react';
import { Outlet } from 'react-router-dom';
import { ModernNavigation } from './ModernNavigation';

export const ModernLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <ModernNavigation />
      {/* Add proper spacing to account for sticky navigation */}
      <main className="pt-0">
        <div className="min-h-[calc(100vh-4rem)]">
          <Outlet />
        </div>
      </main>
    </div>
  );
};