import React from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { ModernLayout } from './components/ModernLayout';
import { ChapterBrowserPage } from './pages/ChapterBrowserPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ExportPage } from './pages/ExportPage';
import { ModernHomePage } from './pages/ModernHomePage';
import { NotFoundPage } from './pages/NotFoundPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { SearchPage } from './pages/SearchPage';
import { StudyPage } from './pages/StudyPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <ModernLayout />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <ModernHomePage />,
      },
      {
        path: 'documents',
        element: <DocumentsPage />,
      },
      {
        path: 'documents/:documentId/chapters',
        element: <ChapterBrowserPage />,
      },
      {
        path: 'study',
        element: <StudyPage />,
      },
      {
        path: 'search',
        element: <SearchPage />,
      },
      {
        path: 'export',
        element: <ExportPage />,
      },
      {
        path: 'privacy',
        element: <PrivacyPage />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);