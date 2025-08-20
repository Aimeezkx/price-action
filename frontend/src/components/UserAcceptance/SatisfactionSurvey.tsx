import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Progress } from '@/components/ui/progress';
import { Star, Heart, ThumbsUp, Zap, Palette, Target } from 'lucide-react';

interface SatisfactionSurveyProps {
  sessionId?: string;
  onSubmit: (survey: any) => void;
  onCancel: () => void;
}

export const SatisfactionSurvey: React.FC<SatisfactionSurveyProps> = ({
  sessionId,
  onSubmit,
  onCancel
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [overallSatisfaction, setOverallSatisfaction] = useState<number | null>(null);
  const [easeOfUse, setEaseOfUse] = useState<number | null>(null);
  const [featureCompleteness, setFeatureCompleteness] = useState<number | null>(null);
  const [performanceSatisfaction, setPerformanceSatisfaction] = useState<number | null>(null);
  const [designSatisfaction, setDesignSatisfaction] = useState<number | null>(null);
  const [likelihoodToRecommend, setLikelihoodToRecommend] = useState<number | null>(null);
  const [mostValuableFeature, setMostValuableFeature] = useState('');
  const [leastValuableFeature, setLeastValuableFeature] = useState('');
  const [improvementSuggestions, setImprovementSuggestions] = useState('');
  const [additionalComments, setAdditionalComments] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const totalSteps = 6;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  const surveySteps = [
    {
      title: 'Overall Satisfaction',
      icon: Heart,
      question: 'How satisfied are you with the application overall?',
      value: overallSatisfaction,
      setValue: setOverallSatisfaction,
      type: 'rating'
    },
    {
      title: 'Ease of Use',
      icon: ThumbsUp,
      question: 'How easy is the application to use?',
      value: easeOfUse,
      setValue: setEaseOfUse,
      type: 'rating'
    },
    {
      title: 'Feature Completeness',
      icon: Target,
      question: 'How complete are the features for your needs?',
      value: featureCompleteness,
      setValue: setFeatureCompleteness,
      type: 'rating'
    },
    {
      title: 'Performance',
      icon: Zap,
      question: 'How satisfied are you with the application performance?',
      value: performanceSatisfaction,
      setValue: setPerformanceSatisfaction,
      type: 'rating'
    },
    {
      title: 'Design',
      icon: Palette,
      question: 'How satisfied are you with the visual design?',
      value: designSatisfaction,
      setValue: setDesignSatisfaction,
      type: 'rating'
    },
    {
      title: 'Recommendation',
      icon: Star,
      question: 'How likely are you to recommend this application to others?',
      subtitle: '(0 = Not at all likely, 10 = Extremely likely)',
      value: likelihoodToRecommend,
      setValue: setLikelihoodToRecommend,
      type: 'nps'
    }
  ];

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);

    try {
      const surveyData = {
        user_id: 'current_user', // Would get from auth context
        session_id: sessionId,
        overall_satisfaction: overallSatisfaction,
        ease_of_use: easeOfUse,
        feature_completeness: featureCompleteness,
        performance_satisfaction: performanceSatisfaction,
        design_satisfaction: designSatisfaction,
        likelihood_to_recommend: likelihoodToRecommend,
        most_valuable_feature: mostValuableFeature,
        least_valuable_feature: leastValuableFeature,
        improvement_suggestions: improvementSuggestions,
        additional_comments: additionalComments
      };

      const response = await fetch('/api/user-acceptance/satisfaction/survey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(surveyData)
      });

      if (response.ok) {
        const result = await response.json();
        onSubmit(result);
      } else {
        throw new Error('Failed to submit survey');
      }
    } catch (error) {
      console.error('Error submitting survey:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderRatingScale = (value: number | null, setValue: (value: number) => void, max: number = 5) => (
    <div className="space-y-4">
      <div className="flex justify-center gap-2">
        {Array.from({ length: max }, (_, i) => i + 1).map((rating) => (
          <button
            key={rating}
            type="button"
            onClick={() => setValue(rating)}
            className={`w-12 h-12 rounded-full border-2 transition-all font-semibold ${
              value === rating
                ? 'bg-blue-500 text-white border-blue-500'
                : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'
            }`}
          >
            {rating}
          </button>
        ))}
      </div>
      
      <div className="flex justify-between text-sm text-gray-600 px-2">
        <span>{max === 5 ? 'Very Poor' : 'Not at all likely'}</span>
        <span>{max === 5 ? 'Excellent' : 'Extremely likely'}</span>
      </div>
      
      {value && (
        <div className="text-center">
          <span className="text-lg font-semibold text-blue-600">
            {max === 5 ? (
              value === 1 ? 'Very Poor' :
              value === 2 ? 'Poor' :
              value === 3 ? 'Average' :
              value === 4 ? 'Good' : 'Excellent'
            ) : (
              value <= 6 ? 'Detractor' :
              value <= 8 ? 'Passive' : 'Promoter'
            )}
          </span>
        </div>
      )}
    </div>
  );

  const currentStepData = surveySteps[currentStep];
  const isCurrentStepComplete = currentStepData?.value !== null;

  if (currentStep >= totalSteps) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Additional Feedback</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="most-valuable">What feature do you find most valuable?</Label>
            <Textarea
              id="most-valuable"
              placeholder="Tell us about the feature you use most or find most helpful..."
              value={mostValuableFeature}
              onChange={(e) => setMostValuableFeature(e.target.value)}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="least-valuable">What feature do you find least valuable?</Label>
            <Textarea
              id="least-valuable"
              placeholder="Is there a feature you rarely use or find confusing?"
              value={leastValuableFeature}
              onChange={(e) => setLeastValuableFeature(e.target.value)}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="improvements">What improvements would you suggest?</Label>
            <Textarea
              id="improvements"
              placeholder="Share your ideas for making the application better..."
              value={improvementSuggestions}
              onChange={(e) => setImprovementSuggestions(e.target.value)}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="additional">Any additional comments?</Label>
            <Textarea
              id="additional"
              placeholder="Anything else you'd like to share?"
              value={additionalComments}
              onChange={(e) => setAdditionalComments(e.target.value)}
              rows={3}
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button onClick={handlePrevious} variant="outline">
              Previous
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={isSubmitting}
              className="flex-1"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Survey'}
            </Button>
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const Icon = currentStepData.icon;

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between mb-4">
          <CardTitle className="flex items-center gap-2">
            <Icon className="h-5 w-5" />
            Satisfaction Survey
          </CardTitle>
          <span className="text-sm text-gray-600">
            {currentStep + 1} of {totalSteps}
          </span>
        </div>
        <Progress value={progress} className="w-full" />
      </CardHeader>
      
      <CardContent className="space-y-8">
        <div className="text-center space-y-4">
          <div className="bg-blue-50 p-6 rounded-lg">
            <Icon className="h-12 w-12 text-blue-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">{currentStepData.title}</h3>
            <p className="text-gray-700">{currentStepData.question}</p>
            {currentStepData.subtitle && (
              <p className="text-sm text-gray-600 mt-2">{currentStepData.subtitle}</p>
            )}
          </div>

          {renderRatingScale(
            currentStepData.value,
            currentStepData.setValue,
            currentStepData.type === 'nps' ? 10 : 5
          )}
        </div>

        <div className="flex gap-2">
          {currentStep > 0 && (
            <Button onClick={handlePrevious} variant="outline">
              Previous
            </Button>
          )}
          
          <Button 
            onClick={handleNext} 
            disabled={!isCurrentStepComplete}
            className="flex-1"
          >
            {currentStep === totalSteps - 1 ? 'Continue to Final Questions' : 'Next'}
          </Button>
          
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};