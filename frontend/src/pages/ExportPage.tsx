import React, { useState } from 'react';

export function ExportPage() {
  const [exportFormat, setExportFormat] = useState<'anki' | 'notion' | 'jsonl'>('anki');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      // TODO: Implement actual export functionality
      console.log('Exporting in format:', exportFormat);
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate export
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div>
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Export</h1>
          <p className="mt-2 text-sm text-gray-700">
            Export your flashcards to other platforms or create backups
          </p>
        </div>
      </div>

      <div className="mt-8 max-w-2xl">
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Export Flashcards
            </h3>
            <div className="mt-2 max-w-xl text-sm text-gray-500">
              <p>Choose your preferred export format and download your flashcards.</p>
            </div>

            <div className="mt-5">
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    id="anki"
                    name="export-format"
                    type="radio"
                    checked={exportFormat === 'anki'}
                    onChange={() => setExportFormat('anki')}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label htmlFor="anki" className="ml-3 block text-sm font-medium text-gray-700">
                    Anki CSV
                    <span className="block text-sm text-gray-500">
                      Compatible with Anki flashcard application
                    </span>
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="notion"
                    name="export-format"
                    type="radio"
                    checked={exportFormat === 'notion'}
                    onChange={() => setExportFormat('notion')}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label htmlFor="notion" className="ml-3 block text-sm font-medium text-gray-700">
                    Notion CSV
                    <span className="block text-sm text-gray-500">
                      Compatible with Notion database import
                    </span>
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="jsonl"
                    name="export-format"
                    type="radio"
                    checked={exportFormat === 'jsonl'}
                    onChange={() => setExportFormat('jsonl')}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <label htmlFor="jsonl" className="ml-3 block text-sm font-medium text-gray-700">
                    JSONL Backup
                    <span className="block text-sm text-gray-500">
                      Complete backup with all metadata for re-import
                    </span>
                  </label>
                </div>
              </div>

              <div className="mt-5">
                <button
                  type="button"
                  onClick={handleExport}
                  disabled={isExporting}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isExporting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Exporting...
                    </>
                  ) : (
                    <>
                      <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Export
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Import Backup
            </h3>
            <div className="mt-2 max-w-xl text-sm text-gray-500">
              <p>Restore your data from a JSONL backup file.</p>
            </div>

            <div className="mt-5">
              <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                    >
                      <span>Upload a backup file</span>
                      <input id="file-upload" name="file-upload" type="file" className="sr-only" accept=".jsonl" />
                    </label>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-gray-500">JSONL files only</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}