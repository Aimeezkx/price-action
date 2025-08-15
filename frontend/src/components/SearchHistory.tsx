import React, { useState } from 'react';
import {
  ClockIcon,
  BookmarkIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import { SearchHistory as SearchHistoryType, SavedSearch } from '../hooks/useSearch';

interface SearchHistoryProps {
  searchHistory: SearchHistoryType[];
  savedSearches: SavedSearch[];
  onLoadFromHistory: (item: SearchHistoryType) => void;
  onSaveSearch: (name: string) => void;
  onLoadSavedSearch: (search: SavedSearch) => void;
  onDeleteSavedSearch: (id: string) => void;
  onClearHistory: () => void;
  currentQuery: string;
}

export function SearchHistory({
  searchHistory,
  savedSearches,
  onLoadFromHistory,
  onSaveSearch,
  onLoadSavedSearch,
  onDeleteSavedSearch,
  onClearHistory,
  currentQuery,
}: SearchHistoryProps) {
  const [showHistory, setShowHistory] = useState(false);
  const [showSaved, setShowSaved] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveName, setSaveName] = useState('');

  const handleSaveSearch = () => {
    if (saveName.trim() && currentQuery.trim()) {
      onSaveSearch(saveName.trim());
      setSaveName('');
      setSaveDialogOpen(false);
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  const getFilterSummary = (filters: any) => {
    const parts = [];
    if (filters.chapter_ids?.length) parts.push(`${filters.chapter_ids.length} chapters`);
    if (filters.knowledge_types?.length) parts.push(`${filters.knowledge_types.length} types`);
    if (filters.card_types?.length) parts.push(`${filters.card_types.length} card types`);
    if (filters.difficulty_min !== undefined || filters.difficulty_max !== undefined) {
      parts.push('difficulty filter');
    }
    return parts.length > 0 ? parts.join(', ') : 'no filters';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">Search Tools</h3>
          {currentQuery.trim() && (
            <button
              type="button"
              onClick={() => setSaveDialogOpen(true)}
              className="inline-flex items-center px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <BookmarkIcon className="h-3 w-3 mr-1" />
              Save Search
            </button>
          )}
        </div>
      </div>

      {/* Saved Searches */}
      <div className="border-b border-gray-200">
        <button
          type="button"
          onClick={() => setShowSaved(!showSaved)}
          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
        >
          <div className="flex items-center">
            <BookmarkSolidIcon className="h-4 w-4 text-blue-500 mr-2" />
            <span className="text-sm font-medium text-gray-900">Saved Searches</span>
            {savedSearches.length > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {savedSearches.length}
              </span>
            )}
          </div>
          {showSaved ? (
            <ChevronUpIcon className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
          )}
        </button>

        {showSaved && (
          <div className="px-4 pb-3">
            {savedSearches.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No saved searches yet. Save your current search to access it later.
              </p>
            ) : (
              <div className="space-y-2">
                {savedSearches.map((search) => (
                  <div
                    key={search.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => onLoadSavedSearch(search)}
                    >
                      <div className="flex items-center space-x-2">
                        <BookmarkSolidIcon className="h-4 w-4 text-blue-500 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {search.name}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            "{search.query}" • {getFilterSummary(search.filters)}
                          </p>
                          <p className="text-xs text-gray-400">
                            Saved {formatDate(search.createdAt)}
                          </p>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => onDeleteSavedSearch(search.id)}
                      className="ml-2 p-1 text-gray-400 hover:text-red-600 focus:outline-none"
                      title="Delete saved search"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Search History */}
      <div>
        <button
          type="button"
          onClick={() => setShowHistory(!showHistory)}
          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
        >
          <div className="flex items-center">
            <ClockIcon className="h-4 w-4 text-gray-500 mr-2" />
            <span className="text-sm font-medium text-gray-900">Recent Searches</span>
            {searchHistory.length > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {searchHistory.length}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {searchHistory.length > 0 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onClearHistory();
                }}
                className="p-1 text-gray-400 hover:text-red-600 focus:outline-none"
                title="Clear history"
              >
                <TrashIcon className="h-3 w-3" />
              </button>
            )}
            {showHistory ? (
              <ChevronUpIcon className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronDownIcon className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </button>

        {showHistory && (
          <div className="px-4 pb-3">
            {searchHistory.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No recent searches. Your search history will appear here.
              </p>
            ) : (
              <div className="space-y-2">
                {searchHistory.slice(0, 10).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                    onClick={() => onLoadFromHistory(item)}
                  >
                    <div className="flex items-center space-x-2 min-w-0 flex-1">
                      <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {item.query}
                        </p>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span>{formatDate(item.timestamp)}</span>
                          {item.resultCount > 0 && (
                            <>
                              <span>•</span>
                              <span>{item.resultCount} results</span>
                            </>
                          )}
                          {getFilterSummary(item.filters) !== 'no filters' && (
                            <>
                              <span>•</span>
                              <span>{getFilterSummary(item.filters)}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {searchHistory.length > 10 && (
                  <p className="text-xs text-gray-500 text-center pt-2">
                    Showing 10 of {searchHistory.length} recent searches
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Save Search Dialog */}
      {saveDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Save Search</h3>
              <button
                type="button"
                onClick={() => setSaveDialogOpen(false)}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Save "{currentQuery}" for quick access later.
              </p>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Name
              </label>
              <input
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="Enter a name for this search..."
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSaveSearch();
                  } else if (e.key === 'Escape') {
                    setSaveDialogOpen(false);
                  }
                }}
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setSaveDialogOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveSearch}
                disabled={!saveName.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}