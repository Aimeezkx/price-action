import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Star, AlertTriangle, Lightbulb, Bug, Zap } from 'lucide-react';

interface FeedbackFormProps {
  sessionId?: string;
  onSubmit: (feedback: any) => void;
  onCancel: () => void;
}

export const FeedbackForm: React.FC<FeedbackFormProps> = ({
  sessionId,
  onSubmit,
  onCancel
}) => {
  const [feedbackType, setFeedbackType] = useState<string>('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState('medium');
  const [satisfactionRating, setSatisfactionRating] = useState<number | null>(null);
  const [easeOfUseRating, setEaseOfUseRating] = useState<number | null>(null);
  const [featureUsefulnessRating, setFeatureUsefulnessRating] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const feedbackTypes = [
    { value: 'bug_report', label: 'Bug Report', icon: Bug, color: 'bg-red-100 text-red-800' },
    { value: 'feature_request', label: 'Feature Request', icon: Lightbulb, color: 'bg-blue-100 text-blue-800' },
    { value: 'usability_issue', label: 'Usability Issue', icon: AlertTriangle, color: 'bg-yellow-100 text-yellow-800' },
    { value: 'performance_complaint', label: 'Performance Issue', icon: Zap, color: 'bg-orange-100 text-orange-800' },
    { value: 'general_feedback', label: 'General Feedback', icon: MessageSquare, color: 'bg-gray-100 text-gray-800' }
  ];

  const severityLevels = [
    { value: 'low', label: 'Low', description: 'Minor issue or suggestion' },
    { value: 'medium', label: 'Medium', description: 'Moderate impact on user experience' },
    { value: 'high', label: 'High', description: 'Significant impact on functionality' },
    { value: 'critical', label: 'Critical', description: 'Blocks core functionality' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const feedbackData = {
        user_id: 'current_user', // Would get from auth context
        session_id: sessionId,
        feedback_type: feedbackType,
        title,
        description,
        severity,
        satisfaction_rating: satisfactionRating,
        ease_of_use_rating: easeOfUseRating,
        feature_usefulness_rating: featureUsefulnessRating
      };

      const response = await fetch('/api/user-acceptance/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackData)
      });

      if (response.ok) {
        const result = await response.json();
        onSubmit(result);
      } else {
        throw new Error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStarRating = (rating: number | null, setRating: (rating: number) => void, label: string) => (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => setRating(star)}
            className={`p-1 rounded transition-colors ${
              rating && star <= rating
                ? 'text-yellow-500'
                : 'text-gray-300 hover:text-yellow-400'
            }`}
          >
            <Star className="h-5 w-5 fill-current" />
          </button>
        ))}
      </div>
      {rating && (
        <p className="text-sm text-gray-600">
          {rating === 1 && 'Very Poor'}
          {rating === 2 && 'Poor'}
          {rating === 3 && 'Average'}
          {rating === 4 && 'Good'}
          {rating === 5 && 'Excellent'}
        </p>
      )}
    </div>
  );

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Share Your Feedback
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Feedback Type */}
          <div className="space-y-3">
            <Label>What type of feedback would you like to share?</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {feedbackTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setFeedbackType(type.value)}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      feedbackType === type.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="h-4 w-4" />
                      <span className="font-medium">{type.label}</span>
                    </div>
                    <Badge className={type.color} variant="secondary">
                      {type.label}
                    </Badge>
                  </button>
                );
              })}
            </div>
          </div>

          {feedbackType && (
            <>
              {/* Title */}
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  placeholder="Brief summary of your feedback"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  placeholder="Please provide detailed information about your feedback..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  required
                />
              </div>

              {/* Severity (for bugs and issues) */}
              {(feedbackType === 'bug_report' || feedbackType === 'usability_issue' || feedbackType === 'performance_complaint') && (
                <div className="space-y-2">
                  <Label>Severity Level</Label>
                  <RadioGroup value={severity} onValueChange={setSeverity}>
                    {severityLevels.map((level) => (
                      <div key={level.value} className="flex items-start space-x-2">
                        <RadioGroupItem value={level.value} id={level.value} className="mt-1" />
                        <div className="flex-1">
                          <Label htmlFor={level.value} className="font-medium">
                            {level.label}
                          </Label>
                          <p className="text-sm text-gray-600">{level.description}</p>
                        </div>
                      </div>
                    ))}
                  </RadioGroup>
                </div>
              )}

              {/* Ratings */}
              <div className="space-y-4">
                <h4 className="font-medium">Rate Your Experience (Optional)</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {renderStarRating(
                    satisfactionRating,
                    setSatisfactionRating,
                    'Overall Satisfaction'
                  )}
                  
                  {renderStarRating(
                    easeOfUseRating,
                    setEaseOfUseRating,
                    'Ease of Use'
                  )}
                  
                  {renderStarRating(
                    featureUsefulnessRating,
                    setFeatureUsefulnessRating,
                    'Feature Usefulness'
                  )}
                </div>
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-2 pt-4">
                <Button 
                  type="submit" 
                  disabled={!title || !description || isSubmitting}
                  className="flex-1"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                </Button>
                <Button type="button" variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              </div>
            </>
          )}
        </form>
      </CardContent>
    </Card>
  );
};