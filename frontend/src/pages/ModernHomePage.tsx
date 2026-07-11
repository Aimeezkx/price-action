import React from 'react';
import { Link } from 'react-router-dom';

export const ModernHomePage: React.FC = () => {
  const features = [
    {
      icon: (
        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      title: 'Upload Documents',
      description: 'Support for PDF, DOCX, and Markdown files with automatic content extraction.',
    },
    {
      icon: (
        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: 'AI Extraction',
      description: 'Automatically extract knowledge points, images, and structure using NLP.',
    },
    {
      icon: (
        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
      title: 'Smart Flashcards',
      description: 'Generate Q&A, cloze deletion, and image hotspot cards automatically.',
    },
    {
      icon: (
        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: 'Spaced Repetition',
      description: 'Optimize learning retention with scientifically-proven spaced repetition.',
    },
  ];

  return (
    <div className="bg-slate-50 min-h-screen">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-extrabold text-blue-700 mb-6">
            Document Learning App
          </h1>

          {/* Enhanced Subtitle */}
          <p className="text-lg md:text-xl text-gray-700 mb-10 max-w-3xl mx-auto leading-relaxed font-medium">
            Transform your documents into interactive learning experiences with
            <span className="text-blue-600 font-semibold"> automated content extraction </span>
            and
            <span className="text-indigo-700 font-semibold"> spaced repetition</span>
          </p>

          {/* Enhanced CTA Buttons */}
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mb-16">
            <Link
              to="/documents"
              className="group bg-blue-700 hover:bg-blue-800 text-white font-semibold px-8 py-3 rounded-xl transition-colors duration-200 text-lg min-w-[180px] shadow-md"
            >
              <span className="flex items-center justify-center gap-2">
                Get Started
                <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
            </Link>
            <Link
              to="/study"
              className="group bg-white hover:bg-gray-50 text-gray-800 font-semibold px-8 py-3 rounded-xl border-2 border-gray-200 hover:border-blue-300 transition-colors duration-200 text-lg min-w-[180px] shadow-md"
            >
              <span className="flex items-center justify-center gap-2">
                Start Studying
                <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.168 18.477 18.582 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </span>
            </Link>
          </div>
        </div>

        {/* Enhanced Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group bg-white rounded-xl p-6 text-center shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-200"
            >
              {/* Enhanced Icon Container */}
              <div className="inline-flex items-center justify-center w-10 h-10 bg-blue-100 rounded-xl mb-4">
                {feature.icon}
              </div>

              {/* Enhanced Feature Title */}
              <h3 className="text-lg font-bold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors duration-300">
                {feature.title}
              </h3>

              {/* Enhanced Feature Description */}
              <p className="text-gray-600 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Additional CTA Section */}
        <div className="mt-16 text-center">
          <div className="bg-white rounded-2xl p-8 shadow-xl border border-gray-100">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
              Ready to revolutionize your learning?
            </h2>
            <p className="text-lg text-gray-600 mb-6 max-w-xl mx-auto">
              Join thousands of learners who have already transformed their study habits with our AI-powered platform.
            </p>
            <Link
              to="/documents"
              className="inline-flex items-center gap-3 bg-indigo-700 hover:bg-indigo-800 text-white font-semibold px-6 py-3 rounded-xl transition-colors duration-200 text-base shadow-md"
            >
              Start Your Journey
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
