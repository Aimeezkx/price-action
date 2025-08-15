import React from 'react';
import { useSearch } from '../hooks/useSearch';
import { SearchInput } from '../components/SearchInput';
import { SearchResults } from '../components/SearchResults';
import { SearchFilters } from '../components/SearchFilters';
import { SearchHistory } from '../components/SearchHistory';

export function SearchPage() {
  const {
    searchState,
    searchResults,
    totalResults,
    isSearching,
    searchError,
    suggestions,
    showSuggestions,
    searchHistory,
    savedSearches,
    setQuery,
    setFilters,
    setOptions,
    toggleAdvanced,
    clearFilters,
    resetSearch,
    search,
    loadFromHistory,
    saveSearch,
    loadSavedSearch,
    deleteSavedSearch,
    clearHistory,
    setShowSuggestions,
  } = useSearch();

  const handleResultClick = (result: any) => {
    // TODO: Navigate to the specific content (knowledge point or card)
    console.log('Clicked result:', result);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="sm:flex sm:items-center mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Search</h1>
          <p className="mt-2 text-sm text-gray-700">
            Find knowledge points and flashcards across your documents
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={resetSearch}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Reset Search
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <SearchFilters
            filters={searchState.filters}
            options={searchState.options}
            onFiltersChange={setFilters}
            onOptionsChange={setOptions}
            onClearFilters={clearFilters}
            isAdvanced={searchState.isAdvanced}
            onToggleAdvanced={toggleAdvanced}
          />
          
          <SearchHistory
            searchHistory={searchHistory}
            savedSearches={savedSearches}
            onLoadFromHistory={loadFromHistory}
            onSaveSearch={saveSearch}
            onLoadSavedSearch={loadSavedSearch}
            onDeleteSavedSearch={deleteSavedSearch}
            onClearHistory={clearHistory}
            currentQuery={searchState.query}
          />
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          <SearchInput
            query={searchState.query}
            onQueryChange={setQuery}
            onSearch={search}
            suggestions={suggestions}
            showSuggestions={showSuggestions}
            onShowSuggestions={setShowSuggestions}
            isSearching={isSearching}
            placeholder="Search knowledge points and flashcards..."
            className="w-full"
          />

          {searchError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Search Error</h3>
                  <p className="mt-1 text-sm text-red-700">
                    {searchError instanceof Error ? searchError.message : 'An error occurred while searching'}
                  </p>
                </div>
              </div>
            </div>
          )}

          <SearchResults
            results={searchResults}
            totalResults={totalResults}
            query={searchState.query}
            isLoading={isSearching}
            onResultClick={handleResultClick}
          />
        </div>
      </div>
    </div>
  );
}