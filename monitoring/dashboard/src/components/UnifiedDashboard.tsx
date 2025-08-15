import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { format, subDays } from 'date-fns';

interface DashboardProps {
  analyticsUrl: string;
}

interface PlatformMetrics {
  web: any;
  ios: any;
  backend: any;
}

interface AlertData {
  id: string;
  platform: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  createdAt: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const UnifiedDashboard: React.FC<DashboardProps> = ({ analyticsUrl }) => {
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedPlatform, setSelectedPlatform] = useState('all');
  const [metrics, setMetrics] = useState<PlatformMetrics>({ web: null, ios: null, backend: null });
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [feedback, setFeedback] = useState<any>(null);
  const [abTests, setAbTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [timeRange, selectedPlatform]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const endDate = new Date();
      const startDate = subDays(endDate, timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : 30);
      
      const params = new URLSearchParams({
        startDate: startDate.toISOString(),
        endDate: endDate.toISOString()
      });

      if (selectedPlatform !== 'all') {
        params.append('platform', selectedPlatform);
      }

      const [
        metricsResponse,
        alertsResponse,
        analyticsResponse,
        feedbackResponse,
        abTestsResponse
      ] = await Promise.all([
        fetch(`${analyticsUrl}/performance/report?${params}`),
        fetch(`${analyticsUrl}/performance/alerts?${params}`),
        fetch(`${analyticsUrl}/analytics/data?${params}`),
        fetch(`${analyticsUrl}/feedback/analysis?${params}`),
        fetch(`${analyticsUrl}/ab-testing/tests/active?${params}`)
      ]);

      const [metricsData, alertsData, analyticsData, feedbackData, abTestsData] = await Promise.all([
        metricsResponse.json(),
        alertsResponse.json(),
        analyticsResponse.json(),
        feedbackResponse.json(),
        abTestsResponse.json()
      ]);

      // Process metrics by platform
      const platformMetrics: PlatformMetrics = { web: {}, ios: {}, backend: {} };
      metricsData.metrics?.forEach((metric: any) => {
        if (!platformMetrics[metric.platform as keyof PlatformMetrics]) {
          platformMetrics[metric.platform as keyof PlatformMetrics] = {};
        }
        platformMetrics[metric.platform as keyof PlatformMetrics][metric.metric_name] = metric;
      });

      setMetrics(platformMetrics);
      setAlerts(alertsData);
      setAnalytics(analyticsData);
      setFeedback(feedbackData);
      setAbTests(abTestsData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderPerformanceMetrics = () => {
    const performanceData = Object.entries(metrics).map(([platform, data]) => ({
      platform,
      responseTime: data?.api_response_time?.avg_value || 0,
      errorRate: data?.error_rate?.avg_value || 0,
      memoryUsage: data?.memory_usage?.avg_value || 0
    }));

    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="platform" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="responseTime" fill="#8884d8" name="Response Time (ms)" />
            <Bar dataKey="errorRate" fill="#82ca9d" name="Error Rate (%)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderAlerts = () => {
    const alertsByPlatform = alerts.reduce((acc, alert) => {
      acc[alert.platform] = (acc[alert.platform] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const alertData = Object.entries(alertsByPlatform).map(([platform, count]) => ({
      platform,
      count
    }));

    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Active Alerts</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={alertData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ platform, count }) => `${platform}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {alertData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded border-l-4 ${
                  alert.severity === 'critical'
                    ? 'border-red-500 bg-red-50'
                    : alert.severity === 'warning'
                    ? 'border-yellow-500 bg-yellow-50'
                    : 'border-blue-500 bg-blue-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-sm">{alert.platform}</p>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    alert.severity === 'critical'
                      ? 'bg-red-100 text-red-800'
                      : alert.severity === 'warning'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderAnalytics = () => {
    const sessionData = analytics?.sessions?.map((session: any) => ({
      platform: session.platform,
      sessions: session.session_count,
      avgDuration: Math.round(session.avg_duration / 60), // Convert to minutes
      avgActions: Math.round(session.avg_actions)
    })) || [];

    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">User Analytics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {sessionData.map((data: any) => (
            <div key={data.platform} className="text-center p-4 bg-gray-50 rounded">
              <h4 className="font-medium text-lg capitalize">{data.platform}</h4>
              <p className="text-2xl font-bold text-blue-600">{data.sessions}</p>
              <p className="text-sm text-gray-600">Sessions</p>
              <p className="text-sm text-gray-600">{data.avgDuration}min avg</p>
            </div>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={sessionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="platform" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="sessions" fill="#8884d8" name="Sessions" />
            <Bar dataKey="avgActions" fill="#82ca9d" name="Avg Actions" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderFeedback = () => {
    const sentimentData = feedback?.sentiment?.map((item: any) => ({
      sentiment: item.sentiment_label,
      count: item.count,
      platform: item.platform
    })) || [];

    const ratingData = feedback?.ratings?.map((item: any) => ({
      rating: item.rating,
      count: item.count
    })) || [];

    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">User Feedback</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-2">Sentiment Analysis</h4>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ sentiment, count }) => `${sentiment}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div>
            <h4 className="font-medium mb-2">Rating Distribution</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={ratingData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="rating" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  const renderABTests = () => {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">A/B Tests</h3>
        <div className="space-y-4">
          {abTests.map((test) => (
            <div key={test.id} className="border rounded p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium">{test.name}</h4>
                  <p className="text-sm text-gray-600">{test.description}</p>
                  <p className="text-sm text-gray-500">
                    Platform: {test.platform} | Participants: {test.participant_count}
                  </p>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                  Active
                </span>
              </div>
            </div>
          ))}
          {abTests.length === 0 && (
            <p className="text-gray-500 text-center py-4">No active A/B tests</p>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Document Learning App - Unified Monitoring
        </h1>
        
        <div className="flex space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          <select
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="all">All Platforms</option>
            <option value="web">Web</option>
            <option value="ios">iOS</option>
            <option value="backend">Backend</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {renderPerformanceMetrics()}
        {renderAlerts()}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {renderAnalytics()}
        {renderFeedback()}
      </div>

      <div className="grid grid-cols-1 gap-6">
        {renderABTests()}
      </div>
    </div>
  );
};