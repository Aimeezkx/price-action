import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend
} from 'recharts';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  Shield,
  Target,
  FileText
} from 'lucide-react';

interface DashboardData {
  timestamp: string;
  executive_summary: ExecutiveSummary;
  overall_status: string;
  overall_pass_rate: number;
  total_tests: number;
  trend_data: TrendData;
  suite_breakdown: SuiteBreakdown;
  performance_metrics: PerformanceMetrics;
  coverage_analysis: CoverageAnalysis;
  issue_summary: IssueSummary;
  last_updated: string;
}

interface ExecutiveSummary {
  overall_health_score: number;
  total_tests_executed: number;
  overall_pass_rate: number;
  critical_issues: number;
  high_priority_issues: number;
  coverage_percentage: number;
  performance_status: string;
  key_achievements: string[];
  top_concerns: string[];
  recommended_actions: string[];
  trend_summary: string;
}

interface TrendData {
  pass_rate_trend: Array<{ date: string; value: number }>;
  coverage_trend: Array<{ date: string; value: number }>;
  duration_trend: Array<{ date: string; value: number }>;
}

interface SuiteBreakdown {
  by_category: Record<string, any>;
  by_status: Record<string, any>;
  suite_details: Array<any>;
}

interface PerformanceMetrics {
  benchmarks: Array<any>;
  summary: {
    total_benchmarks: number;
    passed_benchmarks: number;
    failed_benchmarks: number;
  };
}

interface CoverageAnalysis {
  overall: {
    percentage: number;
    total_lines: number;
    covered_lines: number;
    uncovered_lines: number;
  };
  by_file: Array<{ file: string; coverage: number; status: string }>;
  status: string;
}

interface IssueSummary {
  total_issues: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  recent_issues: Array<any>;
}

const TestDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/test-analysis/dashboard');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard data: ${response.statusText}`);
      }
      
      const data = await response.json();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'passed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Clock className="h-5 w-5 text-blue-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  const getCoverageColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 80) return 'text-yellow-600';
    if (percentage >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-red-700 mb-2">Error Loading Dashboard</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={fetchDashboardData}>Retry</Button>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="text-center py-8">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">No Test Data Available</h3>
        <p className="text-gray-600">Run tests to see dashboard data</p>
      </div>
    );
  }

  const { executive_summary, suite_breakdown, performance_metrics, coverage_analysis, issue_summary, trend_data } = dashboardData;

  // Prepare chart data
  const statusData = Object.entries(suite_breakdown.by_status).map(([status, data]: [string, any]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: data.count,
    percentage: data.percentage
  }));

  const COLORS = {
    passed: '#10B981',
    failed: '#EF4444',
    skipped: '#F59E0B',
    error: '#8B5CF6'
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Test Analysis Dashboard</h1>
          <p className="text-gray-600">
            Last updated: {new Date(dashboardData.last_updated).toLocaleString()}
          </p>
        </div>
        <Button 
          onClick={fetchDashboardData} 
          disabled={refreshing}
          variant="outline"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {/* Executive Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Health Score</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getHealthScoreColor(executive_summary.overall_health_score)}`}>
              {executive_summary.overall_health_score.toFixed(1)}/100
            </div>
            <p className="text-xs text-muted-foreground">
              Overall system health
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {executive_summary.overall_pass_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {executive_summary.total_tests_executed} tests executed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Coverage</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getCoverageColor(executive_summary.coverage_percentage || 0)}`}>
              {(executive_summary.coverage_percentage || 0).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Code coverage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Issues</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {executive_summary.critical_issues}
            </div>
            <p className="text-xs text-muted-foreground">
              {executive_summary.high_priority_issues} high priority
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="coverage">Coverage</TabsTrigger>
          <TabsTrigger value="issues">Issues</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Test Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Test Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase() as keyof typeof COLORS]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Executive Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Executive Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold text-green-700 mb-2">Key Achievements</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {executive_summary.key_achievements.map((achievement, index) => (
                      <li key={index} className="text-sm text-gray-600">{achievement}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-red-700 mb-2">Top Concerns</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {executive_summary.top_concerns.map((concern, index) => (
                      <li key={index} className="text-sm text-gray-600">{concern}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-blue-700 mb-2">Recommended Actions</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {executive_summary.recommended_actions.map((action, index) => (
                      <li key={index} className="text-sm text-gray-600">{action}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Test Suites */}
          <Card>
            <CardHeader>
              <CardTitle>Test Suite Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {suite_breakdown.suite_details.map((suite: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(suite.status)}
                      <div>
                        <h4 className="font-semibold">{suite.name}</h4>
                        <p className="text-sm text-gray-600">
                          {suite.category} • {suite.total_tests} tests • {suite.duration.toFixed(2)}s
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold">
                        {suite.pass_rate.toFixed(1)}%
                      </div>
                      {suite.coverage && (
                        <div className="text-sm text-gray-600">
                          {suite.coverage.toFixed(1)}% coverage
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pass Rate Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Pass Rate Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trend_data.pass_rate_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#10B981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Coverage Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Coverage Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trend_data.coverage_trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Trend Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Trend Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">{executive_summary.trend_summary}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Benchmarks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {performance_metrics.benchmarks.map((benchmark: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-semibold">{benchmark.name}</h4>
                      <p className="text-sm text-gray-600">{benchmark.metric}</p>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-semibold ${benchmark.passed ? 'text-green-600' : 'text-red-600'}`}>
                        {benchmark.value} {benchmark.unit}
                      </div>
                      {benchmark.threshold && (
                        <div className="text-sm text-gray-600">
                          Threshold: {benchmark.threshold} {benchmark.unit}
                        </div>
                      )}
                      <Badge variant={benchmark.passed ? 'default' : 'destructive'}>
                        {benchmark.passed ? 'PASS' : 'FAIL'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="coverage" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Overall Coverage */}
            <Card>
              <CardHeader>
                <CardTitle>Overall Coverage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className={`text-4xl font-bold ${getCoverageColor(coverage_analysis.overall.percentage)}`}>
                      {coverage_analysis.overall.percentage.toFixed(1)}%
                    </div>
                    <p className="text-gray-600">
                      {coverage_analysis.overall.covered_lines} / {coverage_analysis.overall.total_lines} lines covered
                    </p>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${coverage_analysis.overall.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Coverage by File */}
            <Card>
              <CardHeader>
                <CardTitle>Files Needing Attention</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {coverage_analysis.by_file.slice(0, 10).map((file: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div className="truncate flex-1">
                        <span className="text-sm font-mono">{file.file}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-semibold ${getCoverageColor(file.coverage)}`}>
                          {file.coverage.toFixed(1)}%
                        </span>
                        <Badge variant={file.status === 'excellent' ? 'default' : 'secondary'}>
                          {file.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="issues" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Issue Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Issue Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(issue_summary.by_severity).map(([severity, count]) => (
                    <div key={severity} className="flex justify-between items-center">
                      <span className="capitalize">{severity}</span>
                      <Badge variant={severity === 'critical' ? 'destructive' : 'secondary'}>
                        {count}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Issues */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Recent Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {issue_summary.recent_issues.map((issue: any, index: number) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm">{issue.title}</h4>
                          <p className="text-xs text-gray-600 mt-1">{issue.test_case}</p>
                        </div>
                        <div className="flex flex-col items-end space-y-1">
                          <Badge variant={issue.severity === 'critical' ? 'destructive' : 'secondary'}>
                            {issue.severity}
                          </Badge>
                          <span className="text-xs text-gray-500">{issue.category}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TestDashboard;