import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  BarChart3,
  Lightbulb,
  Users,
  Target
} from 'lucide-react';

interface Improvement {
  id: string;
  title: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  status: string;
  estimated_effort: number;
  expected_impact: number;
  confidence: number;
  created_at: string;
}

interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  priority_score: number;
  user_votes: number;
  business_value: number;
  technical_complexity: number;
  estimated_effort: number;
}

interface DashboardData {
  improvements: {
    total: number;
    by_priority: Record<string, number>;
    by_category: Record<string, number>;
    by_status: Record<string, number>;
  };
  feature_requests: {
    total: number;
    total_votes: number;
    average_priority_score: number;
  };
  recent_activity: Array<{
    type: string;
    title: string;
    priority?: string;
    timestamp: string;
  }>;
}

const ImprovementDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [improvements, setImprovements] = useState<Improvement[]>([]);
  const [featureRequests, setFeatureRequests] = useState<FeatureRequest[]>([]);
  const [roiData, setRoiData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard data
      const dashboardResponse = await fetch('/api/improvement/dashboard');
      const dashboard = await dashboardResponse.json();
      setDashboardData(dashboard);

      // Load improvements
      const improvementsResponse = await fetch('/api/improvement/improvements?limit=10');
      const improvementsData = await improvementsResponse.json();
      setImprovements(improvementsData);

      // Load feature requests
      const featuresResponse = await fetch('/api/improvement/feature-requests?limit=10');
      const featuresData = await featuresResponse.json();
      setFeatureRequests(featuresData);

      // Load ROI data
      const roiResponse = await fetch('/api/improvement/roi-analysis');
      const roi = await roiResponse.json();
      setRoiData(roi);

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    try {
      await fetch('/api/improvement/run-analysis', { method: 'POST' });
      // Reload data after analysis
      setTimeout(loadDashboardData, 2000);
    } catch (err) {
      console.error('Analysis error:', err);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        <AlertTriangle className="mx-auto mb-2" size={24} />
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Continuous Improvement</h1>
          <p className="text-gray-600">Monitor and track system improvements</p>
        </div>
        <Button onClick={runAnalysis} className="flex items-center gap-2">
          <BarChart3 size={16} />
          Run Analysis
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Improvements</p>
                <p className="text-2xl font-bold">{dashboardData?.improvements.total || 0}</p>
              </div>
              <Lightbulb className="text-blue-500" size={24} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Feature Requests</p>
                <p className="text-2xl font-bold">{dashboardData?.feature_requests.total || 0}</p>
              </div>
              <Users className="text-green-500" size={24} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Votes</p>
                <p className="text-2xl font-bold">{dashboardData?.feature_requests.total_votes || 0}</p>
              </div>
              <TrendingUp className="text-purple-500" size={24} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">ROI Estimate</p>
                <p className="text-2xl font-bold">{roiData?.roi_percentage?.toFixed(1) || 0}%</p>
              </div>
              <Target className="text-orange-500" size={24} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="improvements" className="space-y-4">
        <TabsList>
          <TabsTrigger value="improvements">Improvements</TabsTrigger>
          <TabsTrigger value="features">Feature Requests</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="activity">Recent Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="improvements" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Priority Improvements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {improvements.map((improvement) => (
                  <div key={improvement.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold">{improvement.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{improvement.description}</p>
                      </div>
                      <Badge className={getPriorityColor(improvement.priority)}>
                        {improvement.priority}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                      <div>
                        <span className="text-gray-500">Category:</span>
                        <p className="font-medium">{improvement.category}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Effort:</span>
                        <p className="font-medium">{improvement.estimated_effort}h</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Impact:</span>
                        <div className="flex items-center gap-2">
                          <Progress value={improvement.expected_impact * 100} className="w-16" />
                          <span>{(improvement.expected_impact * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Confidence:</span>
                        <div className="flex items-center gap-2">
                          <Progress value={improvement.confidence * 100} className="w-16" />
                          <span>{(improvement.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Feature Requests</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {featureRequests.map((request) => (
                  <div key={request.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold">{request.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">Priority Score</div>
                        <div className="font-bold">{request.priority_score.toFixed(1)}</div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                      <div>
                        <span className="text-gray-500">User Votes:</span>
                        <p className="font-medium">{request.user_votes}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Business Value:</span>
                        <div className="flex items-center gap-2">
                          <Progress value={request.business_value * 100} className="w-16" />
                          <span>{(request.business_value * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Complexity:</span>
                        <div className="flex items-center gap-2">
                          <Progress value={request.technical_complexity * 100} className="w-16" />
                          <span>{(request.technical_complexity * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Effort:</span>
                        <p className="font-medium">{request.estimated_effort}h</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Priority Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(dashboardData?.improvements.by_priority || {}).map(([priority, count]) => (
                    <div key={priority} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${getPriorityColor(priority)}`}></div>
                        <span className="capitalize">{priority}</span>
                      </div>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>ROI Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                {roiData && (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Total Improvements:</span>
                      <span className="font-medium">{roiData.total_improvements}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Estimated Cost:</span>
                      <span className="font-medium">${roiData.estimated_cost?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Estimated Benefits:</span>
                      <span className="font-medium">${roiData.estimated_benefits?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>ROI:</span>
                      <span className={`font-medium ${roiData.roi_percentage > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {roiData.roi_percentage?.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Payback Period:</span>
                      <span className="font-medium">
                        {roiData.payback_period_months === Infinity ? 'N/A' : `${roiData.payback_period_months?.toFixed(1)} months`}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {dashboardData?.recent_activity.map((activity, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                    <div className="flex-shrink-0">
                      {activity.type === 'improvement_identified' ? (
                        <Lightbulb className="text-blue-500" size={20} />
                      ) : activity.type === 'improvement_completed' ? (
                        <CheckCircle className="text-green-500" size={20} />
                      ) : (
                        <Clock className="text-gray-500" size={20} />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{activity.title}</p>
                      <p className="text-sm text-gray-500">
                        {activity.type.replace('_', ' ')} • {formatDate(activity.timestamp)}
                      </p>
                    </div>
                    {activity.priority && (
                      <Badge className={getPriorityColor(activity.priority)}>
                        {activity.priority}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ImprovementDashboard;