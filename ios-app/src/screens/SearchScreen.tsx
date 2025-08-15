import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSearch } from '../hooks/useSearch';
import type { SearchResult } from '../types';

export function SearchScreen() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});
  
  const { data: results, isLoading, error, refetch } = useSearch(
    query.trim().length > 0 ? query : undefined,
    filters
  );

  const handleSearch = () => {
    if (query.trim()) {
      refetch();
    }
  };

  const renderResult = ({ item }: { item: SearchResult }) => (
    <TouchableOpacity style={styles.resultItem}>
      <View style={styles.resultHeader}>
        <Text style={styles.resultTitle}>{item.title}</Text>
        <View style={[styles.typeBadge, getTypeStyle(item.type)]}>
          <Text style={styles.typeText}>{item.type}</Text>
        </View>
      </View>
      <Text style={styles.resultContent} numberOfLines={3}>
        {item.content}
      </Text>
      {item.chapter_title && (
        <Text style={styles.chapterTitle}>From: {item.chapter_title}</Text>
      )}
      {item.highlights && item.highlights.length > 0 && (
        <View style={styles.highlightsContainer}>
          {item.highlights.slice(0, 2).map((highlight, index) => (
            <Text key={index} style={styles.highlight}>
              "...{highlight}..."
            </Text>
          ))}
        </View>
      )}
    </TouchableOpacity>
  );

  const getTypeStyle = (type: string) => {
    switch (type) {
      case 'knowledge':
        return { backgroundColor: '#10B981' };
      case 'card':
        return { backgroundColor: '#3B82F6' };
      default:
        return { backgroundColor: '#6B7280' };
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Search Header */}
        <View style={styles.searchHeader}>
          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search knowledge and cards..."
              value={query}
              onChangeText={setQuery}
              onSubmitEditing={handleSearch}
              returnKeyType="search"
            />
            <TouchableOpacity
              style={styles.searchButton}
              onPress={handleSearch}
              disabled={!query.trim() || isLoading}
            >
              <Text style={styles.searchButtonText}>
                {isLoading ? 'Searching...' : 'Search'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Results */}
        <View style={styles.resultsContainer}>
          {!query.trim() ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>Search Your Knowledge</Text>
              <Text style={styles.emptySubtitle}>
                Enter a search term to find relevant knowledge points and flashcards
              </Text>
            </View>
          ) : error ? (
            <View style={styles.errorState}>
              <Text style={styles.errorText}>Search failed</Text>
              <TouchableOpacity style={styles.retryButton} onPress={handleSearch}>
                <Text style={styles.retryButtonText}>Try Again</Text>
              </TouchableOpacity>
            </View>
          ) : results && results.length > 0 ? (
            <>
              <Text style={styles.resultsCount}>
                Found {results.length} result{results.length !== 1 ? 's' : ''}
              </Text>
              <FlatList
                data={results}
                renderItem={renderResult}
                keyExtractor={(item) => `${item.type}-${item.id}`}
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.resultsList}
              />
            </>
          ) : query.trim() && !isLoading ? (
            <View style={styles.noResultsState}>
              <Text style={styles.noResultsTitle}>No results found</Text>
              <Text style={styles.noResultsSubtitle}>
                Try different keywords or check your spelling
              </Text>
            </View>
          ) : null}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  searchHeader: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    height: 44,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
    marginRight: 12,
  },
  searchButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  searchButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  resultsContainer: {
    flex: 1,
    padding: 16,
  },
  resultsCount: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
  },
  resultsList: {
    paddingBottom: 20,
  },
  resultItem: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    flex: 1,
    marginRight: 12,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  typeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
    textTransform: 'capitalize',
  },
  resultContent: {
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 20,
    marginBottom: 8,
  },
  chapterTitle: {
    fontSize: 12,
    color: '#6B7280',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  highlightsContainer: {
    marginTop: 8,
  },
  highlight: {
    fontSize: 12,
    color: '#3B82F6',
    fontStyle: 'italic',
    marginBottom: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
  },
  errorState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  noResultsState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  noResultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  noResultsSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
});