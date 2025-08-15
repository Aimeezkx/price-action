import React, { useRef, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface SearchInputProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  suggestions: string[];
  showSuggestions: boolean;
  onShowSuggestions: (show: boolean) => void;
  isSearching?: boolean;
  placeholder?: string;
  className?: string;
}

export function SearchInput({
  query,
  onQueryChange,
  onSearch,
  suggestions,
  showSuggestions,
  onShowSuggestions,
  isSearching = false,
  placeholder = "Search knowledge points and flashcards...",
  className = "",
}: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onSearch();
      onShowSuggestions(false);
    } else if (e.key === 'Escape') {
      onShowSuggestions(false);
      inputRef.current?.blur();
    } else if (e.key === 'ArrowDown' && showSuggestions && suggestions.length > 0) {
      e.preventDefault();
      const firstSuggestion = suggestionsRef.current?.querySelector('[role="option"]') as HTMLElement;
      firstSuggestion?.focus();
    }
  };

  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: string) => {
    onQueryChange(suggestion);
    onShowSuggestions(false);
    inputRef.current?.focus();
  };

  // Handle suggestion keyboard navigation
  const handleSuggestionKeyDown = (e: React.KeyboardEvent, suggestion: string, index: number) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSuggestionSelect(suggestion);
      onSearch();
    } else if (e.key === 'Escape') {
      onShowSuggestions(false);
      inputRef.current?.focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (index === 0) {
        inputRef.current?.focus();
      } else {
        const prevSuggestion = suggestionsRef.current?.children[index - 1] as HTMLElement;
        prevSuggestion?.focus();
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (index < suggestions.length - 1) {
        const nextSuggestion = suggestionsRef.current?.children[index + 1] as HTMLElement;
        nextSuggestion?.focus();
      }
    }
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        inputRef.current &&
        !inputRef.current.contains(event.target as Node) &&
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node)
      ) {
        onShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onShowSuggestions]);

  const clearQuery = () => {
    onQueryChange('');
    onShowSuggestions(false);
    inputRef.current?.focus();
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) {
              onShowSuggestions(true);
            }
          }}
          placeholder={placeholder}
          className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm placeholder-gray-500"
          disabled={isSearching}
          aria-label="Search input"
          aria-expanded={showSuggestions}
          aria-haspopup="listbox"
          role="combobox"
          autoComplete="off"
        />
        
        <div className="absolute inset-y-0 right-0 flex items-center">
          {query && (
            <button
              type="button"
              onClick={clearQuery}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600"
              aria-label="Clear search"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}
          
          <button
            type="button"
            onClick={onSearch}
            disabled={!query.trim() || isSearching}
            className="ml-1 mr-2 px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Search"
          >
            {isSearching ? (
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              'Search'
            )}
          </button>
        </div>
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto"
          role="listbox"
          aria-label="Search suggestions"
        >
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion}
              role="option"
              tabIndex={0}
              className="px-4 py-2 text-sm text-gray-900 hover:bg-blue-50 focus:bg-blue-50 focus:outline-none cursor-pointer border-b border-gray-100 last:border-b-0"
              onClick={() => handleSuggestionSelect(suggestion)}
              onKeyDown={(e) => handleSuggestionKeyDown(e, suggestion, index)}
            >
              <div className="flex items-center">
                <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                <span className="truncate">{suggestion}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}