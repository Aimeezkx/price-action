import React, { useState, useMemo } from 'react';
import type { Knowledge } from '../types';

interface KnowledgePointBrowserProps {
  knowledgePoints: Knowledge[];
}

export function KnowledgePointBrowser({ knowledgePoints }: KnowledgePointBrowserProps) {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Get unique knowledge types
  const knowledgeTypes = useMemo(() => {
    const types = new Set(knowledgePoints.map(kp => kp.kind));
    return Array.from(types).sort();
  }, [knowledgePoints]);

  // Filter knowledge points
  const filteredKnowledgePoints = useMemo(() => {
    return knowledgePoints.filter(kp => {
      const matchesType = selectedType === 'all' || kp.kind === selectedType;
      const matchesSearch = searchQuery === '' || 
        kp.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        kp.entities.some(entity => entity.toLowerCase().includes(searchQuery.toLowerCase()));
      
      return matchesType && matchesSearch;
    });
  }, [knowledgePoints, selectedType, searchQuery]);

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const getKnowledgeTypeColor = (type: string) => {
    const colors = {
      definition: 'bg-blue-100 text-blue-800',
      fact: 'bg-green-100 text-green-800',
      theorem: 'bg-purple-100 text-purple-800',
      process: 'bg-orange-100 text-orange-800',
      example: 'bg-gray-100 text-gray-800',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getKnowledgeTypeIcon = (type: string) => {
    switch (type) {
      case 'definition':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        );
      case 'fact':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'theorem':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
      case 'process':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'example':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Type Filter */}
        <div className="flex-1">
          <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Filter by Type
          </label>
          <select
            id="type-filter"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="all">All Types ({knowledgePoints.length})</option>
            {knowledgeTypes.map(type => {
              const count = knowledgePoints.filter(kp => kp.kind === type).length;
              return (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)} ({count})
                </option>
              );
            })}
          </select>
        </div>

        {/* Search */}
        <div className="flex-1">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
            Search Knowledge Points
          </label>
          <div className="relative">
            <input
              type="text"
              id="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search text or entities..."
              className="block w-full px-3 py-2 pl-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {filteredKnowledgePoints.length} of {knowledgePoints.length} knowledge points
      </div>

      {/* Knowledge Points List */}
      <div className="space-y-3">
        {filteredKnowledgePoints.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <p className="mt-2">No knowledge points match your filters.</p>
            <button
              onClick={() => {
                setSelectedType('all');
                setSearchQuery('');
              }}
              className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Clear filters
            </button>
          </div>
        ) : (
          filteredKnowledgePoints.map((kp) => (
            <KnowledgePointCard
              key={kp.id}
              knowledgePoint={kp}
              isExpanded={expandedItems.has(kp.id)}
              onToggleExpanded={() => toggleExpanded(kp.id)}
              getTypeColor={getKnowledgeTypeColor}
              getTypeIcon={getKnowledgeTypeIcon}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface KnowledgePointCardProps {
  knowledgePoint: Knowledge;
  isExpanded: boolean;
  onToggleExpanded: () => void;
  getTypeColor: (type: string) => string;
  getTypeIcon: (type: string) => React.ReactNode;
}

function KnowledgePointCard({
  knowledgePoint,
  isExpanded,
  onToggleExpanded,
  getTypeColor,
  getTypeIcon
}: KnowledgePointCardProps) {
  const truncatedText = knowledgePoint.text.length > 200 
    ? knowledgePoint.text.substring(0, 200) + '...'
    : knowledgePoint.text;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(knowledgePoint.kind)}`}>
            {getTypeIcon(knowledgePoint.kind)}
            <span className="ml-1">{knowledgePoint.kind}</span>
          </span>
          
          {knowledgePoint.confidence_score && (
            <span className="text-xs text-gray-500">
              {Math.round(knowledgePoint.confidence_score * 100)}% confidence
            </span>
          )}
        </div>

        {knowledgePoint.text.length > 200 && (
          <button
            onClick={onToggleExpanded}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Content */}
      <div className="mb-3">
        <p className="text-gray-900 leading-relaxed">
          {isExpanded ? knowledgePoint.text : truncatedText}
        </p>
      </div>

      {/* Entities */}
      {knowledgePoint.entities.length > 0 && (
        <div className="mb-3">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Key Entities:</h4>
          <div className="flex flex-wrap gap-1">
            {knowledgePoint.entities.map((entity, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800"
              >
                {entity}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Source Anchors */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
        <div className="flex items-center space-x-4">
          {knowledgePoint.anchors.page && (
            <span className="flex items-center">
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Page {knowledgePoint.anchors.page}
            </span>
          )}
          
          {knowledgePoint.anchors.position && (
            <span className="flex items-center">
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Position {knowledgePoint.anchors.position}
            </span>
          )}
        </div>

        <time dateTime={knowledgePoint.created_at}>
          {new Date(knowledgePoint.created_at).toLocaleDateString()}
        </time>
      </div>
    </div>
  );
}