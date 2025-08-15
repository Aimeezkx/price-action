import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { router } from './router';
import { PerformanceDashboard } from './components/PerformanceDashboard';
import { performanceMonitor } from './lib/performance';

// Track app initialization time
const appStartTime = performance.now();

function App() {
  React.useEffect(() => {
    const appLoadTime = performance.now() - appStartTime;
    performanceMonitor.recordMetric('AppInitialization', appLoadTime);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      {process.env.NODE_ENV === 'development' && <PerformanceDashboard />}
    </QueryClientProvider>
  );
}

export default App;