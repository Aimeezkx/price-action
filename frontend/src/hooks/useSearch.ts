import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { SearchResult } from '../types';

export interface SearchFilters {
  chapter_ids?: string[];
  knowledge_types?: string[];
  card_types?: string[];
  difficulty_min?: number;
  difficulty_max?: number;
  document_ids?: string[];
}

export interface SearchOptions {
  search_type?: 'full_text' | 'semantic' | 'hybrid';
  limit?: number;
  offset?: number;
  similarity_threshold?: number;
}

export interface SearchState {
  query: string;
  filters: SearchFilters;
  options: SearchOptions;
  isAdvanced: boolean;
}

export interface SearchHistory {
  id: string;
  query: string;
  filters: SearchFilters;
  timestamp: Date;
  resultCount: number;
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  options: SearchOptions;
  createdAt: Date;
}

const SEARCH_HISTORY_KEY = 'search_history';
const SAVED_SEARCHES_KEY = 'saved_searches';
const MAX_HISTORY_ITEMS = 50;

export function useSearch() {
  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    filters: {},
    options: {
      search_type: 'hybrid',
      limit: 20,
      offset: 0,
      similarity_threshold: 0.7,
    },
    isAdvanced: false,
  });

  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>(() => {
    try {
      const stored = localStorage.getItem(SEARCH_HISTORY_KEY);
      return stored ? JSON.parse(stored).map((item: any) => ({
        ...item,
        timestamp: new Date(item.timestamp),
      })) : [];
    } catch {
      return [];
    }
  });

  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => {
    try {
      const stored = localStorage.getItem(SAVED_SEARCHES_KEY);
      return stored ? JSON.parse(stored).map((item: any) => ({
        ...item,
        createdAt: new Date(item.createdAt),
      })) : [];
    } catch {
      return [];
    }
  });

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Search query
  const {
    data: searchResults,
    isLoading: isSearching,
    error: searchError,
    refetch: performSearch,
  } = useQuery({
    queryKey: ['search', searchState.query, searchState.filters, searchState.options],
    queryFn: async () => {
      if (!searchState.query.trim()) {
        return { results: [], total_results: 0, suggestions: [] };
      }

      const params = new URLSearchParams({
        query: searchState.query,
        search_type: searchState.options.search_type || 'hybrid',
        limit: String(searchState.options.limit || 20),
        offset: String(searchState.options.offset || 0),
        similarity_threshold: String(searchState.options.similarity_threshold || 0.7),
      });

      // Add filters
      if (searchState.filters.chapter_ids?.length) {
        params.append('chapter_ids', searchState.filters.chapter_ids.join(','));
      }
      if (searchState.filters.knowledge_types?.length) {
        params.append('knowledge_types', searchState.filters.knowledge_types.join(','));
      }
      if (searchState.filters.card_types?.length) {
        params.append('card_types', searchState.filters.card_types.join(','));
      }
      if (searchState.filters.difficulty_min !== undefined) {
        params.append('difficulty_min', String(searchState.filters.difficulty_min));
      }
      if (searchState.filters.difficulty_max !== undefined) {
        params.append('difficulty_max', String(searchState.filters.difficulty_max));
      }
      if (searchState.filters.document_ids?.length) {
        params.append('document_ids', searchState.filters.document_ids.join(','));
      }

      const response = await fetch(`/api/search?${params}`);
      if (!response.ok) {
        throw new Error('Search failed');
      }
      return response.json();
    },
    enabled: false, // Only run when explicitly triggered
  });

  // Get search suggestions
  const getSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/api/search/suggestions?query=${encodeURIComponent(query)}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    }
  }, []);

  // Update search query
  const setQuery = useCallback((query: string) => {
    setSearchState(prev => ({ ...prev, query }));
    getSuggestions(query);
  }, [getSuggestions]);

  // Update filters
  const setFilters = useCallback((filters: Partial<SearchFilters>) => {
    setSearchState(prev => ({
      ...prev,
      filters: { ...prev.filters, ...filters },
    }));
  }, []);

  // Update options
  const setOptions = useCallback((options: Partial<SearchOptions>) => {
    setSearchState(prev => ({
      ...prev,
      options: { ...prev.options, ...options },
    }));
  }, []);

  // Toggle advanced search
  const toggleAdvanced = useCallback(() => {
    setSearchState(prev => ({ ...prev, isAdvanced: !prev.isAdvanced }));
  }, []);

  // Clear filters
  const clearFilters = useCallback(() => {
    setSearchState(prev => ({ ...prev, filters: {} }));
  }, []);

  // Reset search
  const resetSearch = useCallback(() => {
    setSearchState({
      query: '',
      filters: {},
      options: {
        search_type: 'hybrid',
        limit: 20,
        offset: 0,
        similarity_threshold: 0.7,
      },
      isAdvanced: false,
    });
    setSuggestions([]);
    setShowSuggestions(false);
  }, []);

  // Execute search
  const search = useCallback(() => {
    if (!searchState.query.trim()) return;

    performSearch();
    setShowSuggestions(false);

    // Add to search history
    const historyItem: SearchHistory = {
      id: Date.now().toString(),
      query: searchState.query,
      filters: searchState.filters,
      timestamp: new Date(),
      resultCount: 0, // Will be updated when results come back
    };

    setSearchHistory(prev => {
      const newHistory = [historyItem, ...prev.filter(item => item.query !== searchState.query)]
        .slice(0, MAX_HISTORY_ITEMS);
      localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(newHistory));
      return newHistory;
    });
  }, [searchState, performSearch]);

  // Load search from history
  const loadFromHistory = useCallback((historyItem: SearchHistory) => {
    setSearchState(prev => ({
      ...prev,
      query: historyItem.query,
      filters: historyItem.filters,
    }));
  }, []);

  // Save current search
  const saveSearch = useCallback((name: string) => {
    const savedSearch: SavedSearch = {
      id: Date.now().toString(),
      name,
      query: searchState.query,
      filters: searchState.filters,
      options: searchState.options,
      createdAt: new Date(),
    };

    setSavedSearches(prev => {
      const newSaved = [savedSearch, ...prev];
      localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(newSaved));
      return newSaved;
    });
  }, [searchState]);

  // Load saved search
  const loadSavedSearch = useCallback((savedSearch: SavedSearch) => {
    setSearchState(prev => ({
      ...prev,
      query: savedSearch.query,
      filters: savedSearch.filters,
      options: savedSearch.options,
    }));
  }, []);

  // Delete saved search
  const deleteSavedSearch = useCallback((id: string) => {
    setSavedSearches(prev => {
      const newSaved = prev.filter(item => item.id !== id);
      localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(newSaved));
      return newSaved;
    });
  }, []);

  // Clear search history
  const clearHistory = useCallback(() => {
    setSearchHistory([]);
    localStorage.removeItem(SEARCH_HISTORY_KEY);
  }, []);

  // Update result count in history
  useEffect(() => {
    if (searchResults && searchHistory.length > 0) {
      const latestHistory = searchHistory[0];
      if (latestHistory.query === searchState.query && latestHistory.resultCount === 0) {
        const updatedHistory = [
          { ...latestHistory, resultCount: searchResults.total_results },
          ...searchHistory.slice(1),
        ];
        setSearchHistory(updatedHistory);
        localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updatedHistory));
      }
    }
  }, [searchResults, searchHistory, searchState.query]);

  return {
    // State
    searchState,
    searchResults: searchResults?.results || [],
    totalResults: searchResults?.total_results || 0,
    isSearching,
    searchError,
    suggestions,
    showSuggestions,
    searchHistory,
    savedSearches,

    // Actions
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
  };
}