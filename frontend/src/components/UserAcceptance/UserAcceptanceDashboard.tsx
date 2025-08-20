import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Users, 
  MessageSquare, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Star,
  BarChart3,
  TestTube,
  Target
} from 'lucide-react';

interface DashboardData {
  period_days: number;
  generated_at: string;
  summary: {
    active_test_sessions: number;
    active_ab_tests: number;
    total_feedback_items: number;
    satisfaction_responses: number;
  };
  feedback_analysis: any;
  satisfaction_overview: any;
  ux_metrics: any;
  ab_tests: any;
  alerts: Array<{
    type: string;
    severity: string;
    message: string;
    source: string;
  }>;
}

export const UserAcceptanceDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(7);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPeriod]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/user-acceptance/dashboard?days=${selectedPeriod}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const renderMetricCard = (title: string, value: number | string, icon: React.ElementType, trend?: number) => {
    const Icon = icon;
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className="text-2xl font-bold">{value}</p>
              {trend !== undefined && (
                <p className={`text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {trend >= 0 ? '+' : ''}{trend}% from last period
                </p>
              )}
            </div>
            <Icon className="h-8 w-8 text-gray-400" />
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Failed to load dashboard data</p>
        <Button onClick={fetchDashboardData} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">User Acceptance Testing Dashboard</h1>
          <p className="text-gray-600">
            Last {dashboardData.period_days} days • Updated {new Date(dashboardData.generated_at).toLocaleString()}
          </p>
        </div>
        
        <div className="flex gap-2">
          {[7, 14, 30].map((days) => (
            <Button
              key={days}
              variant={selectedPeriod === days ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedPeriod(days)}
            >
              {days}d
            </Button>
          ))}
        </div>
      </div>

      {/* Alerts */}
      {dashboardData.alerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Active Alerts ({dashboardData.alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboardData.alerts.map((alert, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-white rounded border">
                  <div className="flex items-center gap-3">
                    <Badge className={getSeverityColor(alert.severity)}>
                      {alert.severity}
                    </Badge>
                    <span>{alert.message}</span>
                  </div>
                  <Badge variant="outline">{alert.source}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderMetricCard(
          'Active Test Sessions',
          dashboardData.summary.active_test_sessions,
          Users
        )}
        {renderMetricCard(
          'A/B Tests Running',
          dashboardData.summary.active_ab_tests,
          TestTube
        )}
        {renderMetricCard(
          'Feedback Items',
          dashboardData.summary.total_feedback_items,
          MessageSquare
        )}
        {renderMetricCard(
          'Satisfaction Responses',
          dashboardData.summary.satisfaction_responses,
          Star
        )}
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="satisfaction" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="satisfaction">Satisfaction</TabsTrigger>
          <TabsTrigger value="feedback">Feedback</TabsTrigger>
          <TabsTrigger value="ux-metrics">UX Metrics</TabsTrigger>
          <TabsTrigger value="ab-tests">A/B Tests</TabsTrigger>
        </TabsList>

        {/* Satisfaction Tab */}
        <TabsContent value="satisfaction" className="space-y-4">
          {dashboardData.satisfaction_overview && 'error' not in dashboardData.satisfaction_overview ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Satisfaction Scores</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(dashboardData.satisfaction_overview.averages).map(([metric, data]: [string, any]) => (
                    <div key={metric} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium capitalize">
                          {metric.replace('_', ' ')}
                        </span>
                        <span className="text-sm font-bold">
                          {data.mean?.toFixed(1)}/5
                        </span>
                      </div>
                      <Progress value={(data.mean / 5) * 100} className="h-2" />
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Net Promoter Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center space-y-4">
                    <div className="text-4xl font-bold text-blue-600">
                      {dashboardData.satisfaction_overview.nps.score}
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {dashboardData.satisfaction_overview.nps.promoters}
                        </div>
                        <div className="text-gray-600">Promoters</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-600">
                          {dashboardData.satisfaction_overview.nps.passives}
                        </div>
                        <div className="text-gray-600">Passives</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">
                          {dashboardData.satisfaction_overview.nps.detractors}
                        </div>
                        <div className="text-gray-600">Detractors</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-gray-600">No satisfaction data available for this period</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Feedback Tab */}
        <TabsContent value="feedback" className="space-y-4">
          {dashboardData.feedback_analysis && 'error' not in dashboardData.feedback_analysis ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Feedback by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(dashboardData.feedback_analysis.by_type || {}).map(([type, count]: [string, any]) => (
                      <div key={type} className="flex justify-between items-center">
                        <span className="capitalize">{type.replace('_', ' ')}</span>
                        <Badge variant="secondary">{count}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Top Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(dashboardData.feedback_analysis.by_severity || {}).map(([severity, count]: [string, any]) => (
                      <div key={severity} className="flex justify-between items-center">
                        <span className="capitalize">{severity}</span>
                        <Badge className={getSeverityColor(severity)}>{count}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-gray-600">No feedback data available for this period</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* UX Metrics Tab */}
        <TabsContent value="ux-metrics" className="space-y-4">
          {dashboardData.ux_metrics && dashboardData.ux_metrics.key_metrics ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {dashboardData.ux_metrics.key_metrics.avg_page_load_time && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Page Load Time
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {Math.round(dashboardData.ux_metrics.key_metrics.avg_page_load_time)}ms
                    </div>
                    <p className="text-sm text-gray-600">Average load time</p>
                  </CardContent>
                </Card>
              )}

              {dashboardData.ux_metrics.key_metrics.avg_completion_rate && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Task Completion
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {Math.round(dashboardData.ux_metrics.key_metrics.avg_completion_rate * 100)}%
                    </div>
                    <p className="text-sm text-gray-600">Average completion rate</p>
                  </CardContent>
                </Card>
              )}

              {dashboardData.ux_metrics.key_metrics.avg_error_rate && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      Error Rate
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {Math.round(dashboardData.ux_metrics.key_metrics.avg_error_rate * 100)}%
                    </div>
                    <p className="text-sm text-gray-600">Average error rate</p>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-gray-600">No UX metrics data available for this period</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* A/B Tests Tab */}
        <TabsContent value="ab-tests" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Active A/B Tests</CardTitle>
              </CardHeader>
              <CardContent>
                {dashboardData.ab_tests.active_tests.length > 0 ? (
                  <div className="space-y-3">
                    {dashboardData.ab_tests.active_tests.map((test: any) => (
                      <div key={test.id} className="p-3 border rounded">
                        <div className="font-medium">{test.name}</div>
                        <div className="text-sm text-gray-600">{test.feature}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">No active A/B tests</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Test Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Active Tests</span>
                    <Badge>{dashboardData.ab_tests.active_count}</Badge>
                  </div>
                  <div className="text-sm text-gray-600">
                    Monitor your A/B tests to validate feature improvements and user experience changes.
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};