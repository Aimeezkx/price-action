import React, { useState } from 'react';
import { ImageHotspotViewer } from './ImageHotspotViewer';
import type { Hotspot } from '../types';

// Demo hotspots for testing
const demoHotspots: Hotspot[] = [
  {
    id: '1',
    x: 30,
    y: 25,
    width: 12,
    height: 8,
    label: 'Primary Structure',
    description: 'This is the main structural element in the image',
    correct: true,
  },
  {
    id: '2',
    x: 70,
    y: 40,
    width: 10,
    height: 10,
    label: 'Secondary Feature',
    description: 'An important secondary feature to identify',
    correct: true,
  },
  {
    id: '3',
    x: 50,
    y: 70,
    width: 8,
    height: 6,
    label: 'Supporting Element',
    description: 'A supporting element that complements the main structure',
    correct: true,
  },
  {
    id: '4',
    x: 20,
    y: 60,
    width: 6,
    height: 6,
    label: 'Distractor',
    description: 'This looks important but is not a target',
    correct: false,
  },
  {
    id: '5',
    x: 80,
    y: 20,
    width: 5,
    height: 5,
    label: 'Another Distractor',
    description: 'Another element that should not be selected',
    correct: false,
  },
];

export function ImageHotspotDemo() {
  const [mode, setMode] = useState<'study' | 'answer'>('study');
  const [validationResult, setValidationResult] = useState<{
    correct: boolean;
    clickedHotspots: Hotspot[];
  } | null>(null);

  const handleValidationComplete = (correct: boolean, clickedHotspots: Hotspot[]) => {
    setValidationResult({ correct, clickedHotspots });
    console.log('Validation complete:', { correct, clickedHotspots });
  };

  const handleHotspotClick = (hotspot: Hotspot) => {
    console.log('Hotspot clicked:', hotspot);
  };

  const resetDemo = () => {
    setMode('study');
    setValidationResult(null);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Image Hotspot Viewer Demo
        </h1>
        <p className="text-gray-600">
          Interactive image component with zoom, pan, and clickable hotspots
        </p>
      </div>

      {/* Controls */}
      <div className="flex justify-center space-x-4">
        <button
          onClick={() => setMode('study')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'study'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Study Mode
        </button>
        <button
          onClick={() => setMode('answer')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'answer'
              ? 'bg-green-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Answer Mode
        </button>
        <button
          onClick={resetDemo}
          className="px-4 py-2 rounded-lg font-medium bg-gray-500 text-white hover:bg-gray-600 transition-colors"
        >
          Reset
        </button>
      </div>

      {/* Validation Result */}
      {validationResult && (
        <div className={`p-4 rounded-lg ${
          validationResult.correct ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'
        }`}>
          <h3 className={`font-medium ${
            validationResult.correct ? 'text-green-800' : 'text-yellow-800'
          }`}>
            {validationResult.correct ? '🎉 Perfect!' : '⚠️ Partial Success'}
          </h3>
          <p className={`text-sm mt-1 ${
            validationResult.correct ? 'text-green-700' : 'text-yellow-700'
          }`}>
            You clicked {validationResult.clickedHotspots.length} hotspot(s). 
            {validationResult.correct 
              ? ' All selections were correct!'
              : ' Some selections were incorrect, but you found all the key areas.'
            }
          </p>
          <div className="mt-2">
            <p className="text-xs font-medium text-gray-600 mb-1">Selected hotspots:</p>
            <div className="flex flex-wrap gap-1">
              {validationResult.clickedHotspots.map(hotspot => (
                <span
                  key={hotspot.id}
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    hotspot.correct
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {hotspot.label}
                  {hotspot.correct ? ' ✓' : ' ✗'}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Demo Image with Hotspots */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <ImageHotspotViewer
          imageSrc="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjQwMCIgdmlld0JveD0iMCAwIDYwMCA0MDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI2MDAiIGhlaWdodD0iNDAwIiBmaWxsPSIjRjNGNEY2Ii8+CjxyZWN0IHg9IjE1MCIgeT0iODAiIHdpZHRoPSI4MCIgaGVpZ2h0PSI0MCIgZmlsbD0iIzM5OEVGNyIgcng9IjQiLz4KPHJlY3QgeD0iMzgwIiB5PSIxNDAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgZmlsbD0iIzEwQjk4MSIgcng9IjgiLz4KPHJlY3QgeD0iMjcwIiB5PSIyNjAiIHdpZHRoPSI1MCIgaGVpZ2h0PSIzMCIgZmlsbD0iI0Y1OUUwQiIgcng9IjQiLz4KPHJlY3QgeD0iMTAwIiB5PSIyMjAiIHdpZHRoPSI0MCIgaGVpZ2h0PSIzMCIgZmlsbD0iI0VGNDQ0NCIgcng9IjQiLz4KPHJlY3QgeD0iNDUwIiB5PSI2MCIgd2lkdGg9IjMwIiBoZWlnaHQ9IjMwIiBmaWxsPSIjOEI1Q0Y2IiByeD0iNCIvPgo8dGV4dCB4PSIzMDAiIHk9IjIwMCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSIjMzc0MTUxIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5EZW1vIEltYWdlIHdpdGggSG90c3BvdHM8L3RleHQ+Cjx0ZXh0IHg9IjMwMCIgeT0iMjI1IiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2QjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkNsaWNrIG9uIHRoZSBjb2xvcmVkIHNoYXBlcyB0byBpbnRlcmFjdCE8L3RleHQ+Cjwvc3ZnPgo="
          hotspots={demoHotspots}
          mode={mode}
          onHotspotClick={handleHotspotClick}
          onValidationComplete={handleValidationComplete}
          className="w-full"
          maxZoom={3}
          minZoom={0.5}
          zoomStep={1.3}
          enableKeyboardControls={true}
        />
      </div>

      {/* Feature List */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Zoom and pan with mouse/touch</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Clickable hotspot regions</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Hover effects and tooltips</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Touch gesture support</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Keyboard controls (+, -, 0, arrows)</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Validation and feedback system</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Responsive design</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="text-green-500">✓</span>
              <span>Accessibility support</span>
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Instructions</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <div>
              <p className="font-medium text-gray-800">Study Mode:</p>
              <p>Click on the colored shapes to select them. Find all 3 correct areas!</p>
            </div>
            <div>
              <p className="font-medium text-gray-800">Answer Mode:</p>
              <p>View the correct answers highlighted in green.</p>
            </div>
            <div>
              <p className="font-medium text-gray-800">Navigation:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Mouse wheel or pinch to zoom</li>
                <li>Drag to pan when zoomed in</li>
                <li>Double-click to zoom in/out</li>
                <li>Use keyboard: +/- to zoom, arrows to pan</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}