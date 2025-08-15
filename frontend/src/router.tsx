import React from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ChapterBrowserPage } from './pages/ChapterBrowserPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ExportPage } from './pages/ExportPage';
import { HomePage } from './pages/HomePage';
import { NotFoundPage } from './pages/NotFoundPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { SearchPage } from './pages/SearchPage';
import { StudyPage } from './pages/StudyPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <HomePage />,
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