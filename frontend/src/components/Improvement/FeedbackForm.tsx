import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Star, Send, CheckCircle } from 'lucide-react';

interface FeedbackFormProps {
  onSubmit?: (feedback: any) => void;
  className?: string;
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({ onSubmit, className }) => {
  const [formData, setFormData] = useState({
    feature: '',
    rating: 0,
    comment: '',
    category: '',
    severity: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const features = [
    'Document Upload',
    'Document Processing',
    'Card Generation',
    'Study Interface',
    'Search Functionality',
    'Chapter Navigation',
    'Performance',
    'User Interface',
    'Mobile Experience',
    'Export Features',
    'Other'
  ];

  const categories = [
    'bug',
    'performance',
    'usability',
    'feature_request',
    'ui_design',
    'accessibility',
    'mobile',
    'general'
  ];

  const severities = [
    'low',
    'medium',
    'high',
    'critical'
  ];

  const handleRatingClick = (rating: number) => {
    setFormData(prev => ({ ...prev, rating }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.feature || !formData.rating || !formData.comment.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    if (formData.comment.length < 10) {
      setError('Please provide more detailed feedback (at least 10 characters)');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/improvement/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit feedback');
      }

      const result = await response.json();
      
      setIsSubmitted(true);
      
      // Reset form after successful submission
      setTimeout(() => {
        setFormData({
          feature: '',
          rating: 0,
          comment: '',
          category: '',
          severity: ''
        });
        setIsSubmitted(false);
      }, 3000);

      if (onSubmit) {
        onSubmit(result);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <CheckCircle className="mx-auto text-green-500" size={48} />
            <h3 className="text-lg font-semibold text-green-700">Thank You!</h3>
            <p className="text-gray-600">
              Your feedback has been submitted successfully. We appreciate your input and will use it to improve the system.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send size={20} />
          Submit Feedback
        </CardTitle>
        <p className="text-sm text-gray-600">
          Help us improve by sharing your experience and suggestions
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Feature Selection */}
          <div className="space-y-2">
            <Label htmlFor="feature">Feature/Area *</Label>
            <Select 
              value={formData.feature} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, feature: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select the feature you're providing feedback about" />
              </SelectTrigger>
              <SelectContent>
                {features.map((feature) => (
                  <SelectItem key={feature} value={feature}>
                    {feature}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Rating */}
          <div className="space-y-2">
            <Label>Rating *</Label>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => handleRatingClick(star)}
                  className={`p-1 rounded transition-colors ${
                    star <= formData.rating 
                      ? 'text-yellow-500 hover:text-yellow-600' 
                      : 'text-gray-300 hover:text-gray-400'
                  }`}
                >
                  <Star 
                    size={24} 
                    fill={star <= formData.rating ? 'currentColor' : 'none'}
                  />
                </button>
              ))}
              <span className="ml-2 text-sm text-gray-600">
                {formData.rating > 0 && (
                  <>
                    {formData.rating}/5 - {
                      formData.rating === 5 ? 'Excellent' :
                      formData.rating === 4 ? 'Good' :
                      formData.rating === 3 ? 'Average' :
                      formData.rating === 2 ? 'Poor' : 'Very Poor'
                    }
                  </>
                )}
              </span>
            </div>
          </div>

          {/* Comment */}
          <div className="space-y-2">
            <Label htmlFor="comment">Detailed Feedback *</Label>
            <Textarea
              id="comment"
              placeholder="Please describe your experience, any issues you encountered, or suggestions for improvement..."
              value={formData.comment}
              onChange={(e) => setFormData(prev => ({ ...prev, comment: e.target.value }))}
              rows={4}
              className="resize-none"
            />
            <div className="text-xs text-gray-500">
              {formData.comment.length}/500 characters (minimum 10 required)
            </div>
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category (Optional)</Label>
            <Select 
              value={formData.category} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Categorize your feedback" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Severity (only show for low ratings) */}
          {formData.rating <= 3 && formData.rating > 0 && (
            <div className="space-y-2">
              <Label htmlFor="severity">Issue Severity</Label>
              <Select 
                value={formData.severity} 
                onValueChange={(value) => setFormData(prev => ({ ...prev, severity: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="How severe is this issue?" />
                </SelectTrigger>
                <SelectContent>
                  {severities.map((severity) => (
                    <SelectItem key={severity} value={severity}>
                      {severity.charAt(0).toUpperCase() + severity.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button 
            type="submit" 
            disabled={isSubmitting}
            className="w-full"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Submitting...
              </>
            ) : (
              <>
                <Send size={16} className="mr-2" />
                Submit Feedback
              </>
            )}
          </Button>
        </form>

        {/* Help Text */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-700">
            <strong>Your feedback helps us:</strong> Identify bugs, improve performance, 
            enhance user experience, and prioritize new features. All feedback is reviewed 
            and contributes to our continuous improvement process.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default FeedbackForm;