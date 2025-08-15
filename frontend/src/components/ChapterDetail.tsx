import React, { useState } from 'react';
import { useChapterFigures, useChapterKnowledge } from '../hooks/useChapters';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import { ImageViewer } from './ImageViewer';
import { KnowledgePointBrowser } from './KnowledgePointBrowser';
import type { Figure, Knowledge } from '../types';

interface ChapterDetailProps {
  chapterId: string;
  chapterTitle: string;
}

export function ChapterDetail({ chapterId, chapterTitle }: ChapterDetailProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'figures' | 'knowledge'>('overview');
  const [selectedImage, setSelectedImage] = useState<Figure | null>(null);

  const { 
    data: figuresData, 
    isLoading: figuresLoading, 
    error: figuresError 
  } = useChapterFigures(chapterId);

  const { 
    data: knowledgeData, 
    isLoading: knowledgeLoading, 
    error: knowledgeError 
  } = useChapterKnowledge(chapterId, { limit: 50 });

  const tabs = [
    { id: 'overview', name: 'Overview', count: null },
    { id: 'figures', name: 'Figures', count: figuresData?.total_figures || 0 },
    { id: 'knowledge', name: 'Knowledge Points', count: knowledgeData?.total_knowledge_points || 0 },
  ] as const;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">{chapterTitle}</h2>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.name}
              {tab.count !== null && (
                <span className={`
                  ml-2 py-0.5 px-2 rounded-full text-xs
                  ${activeTab === tab.id
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-gray-100 text-gray-900'
                  }
                `}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <ChapterOverview 
            figuresCount={figuresData?.total_figures || 0}
            knowledgeCount={knowledgeData?.total_knowledge_points || 0}
            onViewFigures={() => setActiveTab('figures')}
            onViewKnowledge={() => setActiveTab('knowledge')}
          />
        )}

        {activeTab === 'figures' && (
          <FiguresTab
            figuresData={figuresData}
            isLoading={figuresLoading}
            error={figuresError}
            onImageClick={setSelectedImage}
          />
        )}

        {activeTab === 'knowledge' && (
          <KnowledgeTab
            knowledgeData={knowledgeData}
            isLoading={knowledgeLoading}
            error={knowledgeError}
          />
        )}
      </div>

      {/* Image Viewer Modal */}
      {selectedImage && (
        <ImageViewer
          figure={selectedImage}
          onClose={() => setSelectedImage(null)}
        />
      )}
    </div>
  );
}

interface ChapterOverviewProps {
  figuresCount: number;
  knowledgeCount: number;
  onViewFigures: () => void;
  onViewKnowledge: () => void;
}

function ChapterOverview({ 
  figuresCount, 
  knowledgeCount, 
  onViewFigures, 
  onViewKnowledge 
}: ChapterOverviewProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Figures Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Figures</h3>
              <p className="text-sm text-gray-600 mt-1">
                {figuresCount} image{figuresCount !== 1 ? 's' : ''} with captions
              </p>
            </div>
            <div className="text-2xl font-bold text-blue-600">{figuresCount}</div>
          </div>
          {figuresCount > 0 && (
            <button
              onClick={onViewFigures}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              View all figures →
            </button>
          )}
        </div>

        {/* Knowledge Points Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Knowledge Points</h3>
              <p className="text-sm text-gray-600 mt-1">
                Extracted concepts and definitions
              </p>
            </div>
            <div className="text-2xl font-bold text-green-600">{knowledgeCount}</div>
          </div>
          {knowledgeCount > 0 && (
            <button
              onClick={onViewKnowledge}
              className="mt-3 text-sm text-green-600 hover:text-green-800 font-medium"
            >
              Browse knowledge points →
            </button>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Generate Cards
          </button>
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Search Content
          </button>
        </div>
      </div>
    </div>
  );
}

interface FiguresTabProps {
  figuresData: any;
  isLoading: boolean;
  error: any;
  onImageClick: (figure: Figure) => void;
}

function FiguresTab({ figuresData, isLoading, error, onImageClick }: FiguresTabProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage message="Failed to load figures" />
    );
  }

  if (!figuresData || figuresData.figures.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p className="mt-2">No figures found in this chapter.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {figuresData.figures.map((figure: Figure) => (
        <div
          key={figure.id}
          className="bg-gray-50 rounded-lg overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => onImageClick(figure)}
        >
          <div className="aspect-w-16 aspect-h-9 bg-gray-200">
            <img
              src={`/api/files/${figure.image_path}`}
              alt={figure.caption || 'Figure'}
              className="w-full h-48 object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgMTZsNC41ODYtNC41ODZhMiAyIDAgMDEyLjgyOCAwTDE2IDE2bS0yLTJsMS41ODYtMS41ODZhMiAyIDAgMDEyLjgyOCAwTDIwIDE0bS02LTZoLjAxTTYgMjBoMTJhMiAyIDAgMDAyLTJWNmEyIDIgMCAwMC0yLTJINmEyIDIgMCAwMC0yIDJ2MTJhMiAyIDAgMDAyIDJ6IiBzdHJva2U9IiM5Q0E3QjAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=';
              }}
            />
          </div>
          <div className="p-4">
            <p className="text-sm text-gray-600 mb-2">Page {figure.page_number}</p>
            <p className="text-sm text-gray-900 overflow-hidden" style={{ 
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical'
            }}>
              {figure.caption || 'No caption available'}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

interface KnowledgeTabProps {
  knowledgeData: any;
  isLoading: boolean;
  error: any;
}

function KnowledgeTab({ knowledgeData, isLoading, error }: KnowledgeTabProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage message="Failed to load knowledge points" />
    );
  }

  if (!knowledgeData || knowledgeData.knowledge_points.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p className="mt-2">No knowledge points found in this chapter.</p>
      </div>
    );
  }

  return (
    <KnowledgePointBrowser knowledgePoints={knowledgeData.knowledge_points} />
  );
}