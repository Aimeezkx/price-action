import React, { useState, useEffect } from 'react';
import { Shield, Eye, EyeOff, AlertTriangle, CheckCircle, Settings } from 'lucide-react';

interface PrivacyStatus {
  privacy_configuration: {
    privacy_mode: boolean;
    anonymize_logs: boolean;
    use_llm: boolean;
    enable_file_scanning: boolean;
    external_services: {
      llm: boolean;
      ocr: boolean;
      embeddings: string;
    };
  };
  warnings: string[];
  security_features: {
    file_validation: boolean;
    rate_limiting: boolean;
    secure_logging: boolean;
    malware_scanning: boolean;
  };
}

export const PrivacySettings: React.FC = () => {
  const [privacyStatus, setPrivacyStatus] = useState<PrivacyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrivacyStatus = async () => {
    try {
      const response = await fetch('/api/privacy/status');
      if (!response.ok) {
        throw new Error('Failed to fetch privacy status');
      }
      const data = await response.json();
      setPrivacyStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const togglePrivacyMode = async (enable: boolean) => {
    setToggling(true);
    try {
      const response = await fetch(`/api/privacy/toggle?enable=${enable}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to toggle privacy mode');
      }
      
      // Refresh status after toggle
      await fetchPrivacyStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle privacy mode');
    } finally {
      setToggling(false);
    }
  };

  useEffect(() => {
    fetchPrivacyStatus();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading privacy settings...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">Error: {error}</span>
        </div>
        <button
          onClick={fetchPrivacyStatus}
          className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!privacyStatus) {
    return null;
  }

  const { privacy_configuration, warnings, security_features } = privacyStatus;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <Shield className="h-6 w-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Privacy & Security Settings</h2>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Privacy Mode Toggle */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              {privacy_configuration.privacy_mode ? (
                <EyeOff className="h-5 w-5 text-green-600 mr-3" />
              ) : (
                <Eye className="h-5 w-5 text-orange-600 mr-3" />
              )}
              <div>
                <h3 className="font-medium text-gray-900">Privacy Mode</h3>
                <p className="text-sm text-gray-600">
                  {privacy_configuration.privacy_mode
                    ? 'All processing is done locally. No data sent to external services.'
                    : 'External services may be used for enhanced processing capabilities.'}
                </p>
              </div>
            </div>
            <button
              onClick={() => togglePrivacyMode(!privacy_configuration.privacy_mode)}
              disabled={toggling}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                privacy_configuration.privacy_mode ? 'bg-green-600' : 'bg-gray-300'
              } ${toggling ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  privacy_configuration.privacy_mode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-800">Privacy Warnings</h4>
                  <ul className="mt-2 text-sm text-yellow-700 space-y-1">
                    {warnings.map((warning, index) => (
                      <li key={index}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Security Features Status */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Security Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(security_features).map(([feature, enabled]) => (
                <div key={feature} className="flex items-center p-3 bg-gray-50 rounded-lg">
                  {enabled ? (
                    <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
                  )}
                  <div>
                    <span className="font-medium text-gray-900 capitalize">
                      {feature.replace(/_/g, ' ')}
                    </span>
                    <span className={`ml-2 text-sm ${enabled ? 'text-green-600' : 'text-red-600'}`}>
                      {enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* External Services Status */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">External Services</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-900">Large Language Model (LLM)</span>
                <span className={`text-sm px-2 py-1 rounded ${
                  privacy_configuration.external_services.llm
                    ? 'bg-orange-100 text-orange-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {privacy_configuration.external_services.llm ? 'External' : 'Local Only'}
                </span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-900">Optical Character Recognition (OCR)</span>
                <span className={`text-sm px-2 py-1 rounded ${
                  privacy_configuration.external_services.ocr
                    ? 'bg-orange-100 text-orange-800'
                    : 'bg-green-100 text-green-800'
                }`}>
                  {privacy_configuration.external_services.ocr ? 'External' : 'Disabled'}
                </span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-900">Text Embeddings</span>
                <span className="text-sm px-2 py-1 rounded bg-green-100 text-green-800">
                  {privacy_configuration.external_services.embeddings}
                </span>
              </div>
            </div>
          </div>

          {/* Configuration Details */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Configuration Details</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="font-medium text-gray-900">Log Anonymization</dt>
                  <dd className={privacy_configuration.anonymize_logs ? 'text-green-600' : 'text-red-600'}>
                    {privacy_configuration.anonymize_logs ? 'Enabled' : 'Disabled'}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-900">File Scanning</dt>
                  <dd className={privacy_configuration.enable_file_scanning ? 'text-green-600' : 'text-red-600'}>
                    {privacy_configuration.enable_file_scanning ? 'Enabled' : 'Disabled'}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-900">LLM Processing</dt>
                  <dd className={privacy_configuration.use_llm ? 'text-orange-600' : 'text-green-600'}>
                    {privacy_configuration.use_llm ? 'Enabled' : 'Disabled'}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-900">Privacy Mode</dt>
                  <dd className={privacy_configuration.privacy_mode ? 'text-green-600' : 'text-orange-600'}>
                    {privacy_configuration.privacy_mode ? 'Enabled' : 'Disabled'}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Refresh Button */}
          <div className="flex justify-end">
            <button
              onClick={fetchPrivacyStatus}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <Settings className="h-4 w-4 mr-2" />
              Refresh Status
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacySettings;