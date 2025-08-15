import React from 'react';

interface GradingInterfaceProps {
  onGrade: (grade: number) => void;
  disabled?: boolean;
  className?: string;
}

const gradeOptions = [
  { value: 0, label: 'Again', description: 'Complete blackout', color: 'bg-red-500 hover:bg-red-600' },
  { value: 1, label: 'Hard', description: 'Incorrect, but remembered', color: 'bg-orange-500 hover:bg-orange-600' },
  { value: 2, label: 'Good', description: 'Correct with hesitation', color: 'bg-yellow-500 hover:bg-yellow-600' },
  { value: 3, label: 'Easy', description: 'Correct with some thought', color: 'bg-green-500 hover:bg-green-600' },
  { value: 4, label: 'Perfect', description: 'Correct immediately', color: 'bg-blue-500 hover:bg-blue-600' },
  { value: 5, label: 'Too Easy', description: 'Trivially easy', color: 'bg-purple-500 hover:bg-purple-600' },
];

export function GradingInterface({ onGrade, disabled = false, className = '' }: GradingInterfaceProps) {
  const handleKeyPress = (event: React.KeyboardEvent) => {
    const key = event.key;
    if (key >= '0' && key <= '5') {
      const grade = parseInt(key, 10);
      onGrade(grade);
    }
  };

  return (
    <div className={`w-full max-w-2xl mx-auto ${className}`} onKeyDown={handleKeyPress} tabIndex={0}>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            How well did you know this?
          </h3>
          <p className="text-sm text-gray-500">
            Use keyboard shortcuts 0-5 or click the buttons below
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {gradeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => onGrade(option.value)}
              disabled={disabled}
              className={`
                ${option.color} text-white font-medium py-3 px-4 rounded-lg
                transition-all duration-200 transform
                hover:scale-105 active:scale-95
                disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
              `}
            >
              <div className="text-center">
                <div className="text-lg font-bold">{option.value}</div>
                <div className="text-sm font-medium">{option.label}</div>
                <div className="text-xs opacity-90 mt-1">{option.description}</div>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-100">
          <div className="flex justify-center space-x-6 text-sm text-gray-500">
            <div className="flex items-center">
              <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono mr-2">0-5</kbd>
              Grade card
            </div>
            <div className="flex items-center">
              <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono mr-2">Space</kbd>
              Flip card
            </div>
            <div className="flex items-center">
              <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono mr-2">J/K</kbd>
              Navigate
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}