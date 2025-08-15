import React from 'react';

export interface CardFilters {
  chapter?: string;
  difficulty?: string;
  cardType?: string;
}

interface CardFiltersProps {
  filters: CardFilters;
  onFiltersChange: (filters: CardFilters) => void;
  chapters?: Array<{ id: string; title: string }>;
  className?: string;
}

const difficultyOptions = [
  { value: '', label: 'All Difficulties' },
  { value: 'easy', label: 'Easy (≤1.5)' },
  { value: 'medium', label: 'Medium (1.5-2.5)' },
  { value: 'hard', label: 'Hard (>2.5)' },
];

const cardTypeOptions = [
  { value: '', label: 'All Types' },
  { value: 'qa', label: 'Q&A Cards' },
  { value: 'cloze', label: 'Cloze Deletion' },
  { value: 'image_hotspot', label: 'Image Hotspot' },
];

export function CardFilters({ 
  filters, 
  onFiltersChange, 
  chapters = [], 
  className = '' 
}: CardFiltersProps) {
  const handleFilterChange = (key: keyof CardFilters, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      <div className="flex flex-wrap gap-4">
        {/* Chapter Filter */}
        <div className="flex-1 min-w-48">
          <label htmlFor="chapter-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Chapter
          </label>
          <select
            id="chapter-filter"
            value={filters.chapter || ''}
            onChange={(e) => handleFilterChange('chapter', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="">All Chapters</option>
            {chapters.map((chapter) => (
              <option key={chapter.id} value={chapter.id}>
                {chapter.title}
              </option>
            ))}
          </select>
        </div>

        {/* Difficulty Filter */}
        <div className="flex-1 min-w-48">
          <label htmlFor="difficulty-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Difficulty
          </label>
          <select
            id="difficulty-filter"
            value={filters.difficulty || ''}
            onChange={(e) => handleFilterChange('difficulty', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            {difficultyOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Card Type Filter */}
        <div className="flex-1 min-w-48">
          <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Card Type
          </label>
          <select
            id="type-filter"
            value={filters.cardType || ''}
            onChange={(e) => handleFilterChange('cardType', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            {cardTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Clear Filters Button */}
        <div className="flex items-end">
          <button
            onClick={() => onFiltersChange({})}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Active Filters Display */}
      {(filters.chapter || filters.difficulty || filters.cardType) && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-500">Active filters:</span>
            {filters.chapter && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Chapter: {chapters.find(c => c.id === filters.chapter)?.title || filters.chapter}
                <button
                  onClick={() => handleFilterChange('chapter', '')}
                  className="ml-1 text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            )}
            {filters.difficulty && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                {difficultyOptions.find(d => d.value === filters.difficulty)?.label}
                <button
                  onClick={() => handleFilterChange('difficulty', '')}
                  className="ml-1 text-green-600 hover:text-green-800"
                >
                  ×
                </button>
              </span>
            )}
            {filters.cardType && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                {cardTypeOptions.find(t => t.value === filters.cardType)?.label}
                <button
                  onClick={() => handleFilterChange('cardType', '')}
                  className="ml-1 text-purple-600 hover:text-purple-800"
                >
                  ×
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}