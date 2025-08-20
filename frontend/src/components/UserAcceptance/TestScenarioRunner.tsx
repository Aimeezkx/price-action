import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { CheckCircle, Clock, AlertCircle, Play, Pause, Square } from 'lucide-react';

interface TestStep {
  description: string;
  expectedOutcome: string;
  completed: boolean;
  startTime?: number;
  endTime?: number;
}

interface TestScenario {
  id: string;
  name: string;
  description: string;
  steps: string[];
  expectedOutcomes: string[];
  successCriteria: string[];
  estimatedDuration: number;
}

interface TestSession {
  id: string;
  scenarioId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  completionRate: number;
  currentStep: number;
}

interface TestScenarioRunnerProps {
  scenario: TestScenario;
  onComplete: (result: any) => void;
  onCancel: () => void;
}

export const TestScenarioRunner: React.FC<TestScenarioRunnerProps> = ({
  scenario,
  onComplete,
  onCancel
}) => {
  const [session, setSession] = useState<TestSession | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [stepStartTime, setStepStartTime] = useState<number | null>(null);
  const [completedSteps, setCompletedSteps] = useState<TestStep[]>([]);
  const [feedback, setFeedback] = useState('');
  const [satisfaction, setSatisfaction] = useState<string>('');
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    // Initialize test steps
    const steps: TestStep[] = scenario.steps.map((step, index) => ({
      description: step,
      expectedOutcome: scenario.expectedOutcomes[index] || '',
      completed: false
    }));
    setCompletedSteps(steps);
  }, [scenario]);

  const startTest = async () => {
    try {
      const response = await fetch('/api/user-acceptance/sessions/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current_user', // Would get from auth context
          scenario_id: scenario.id
        })
      });

      if (response.ok) {
        const newSession = await response.json();
        setSession(newSession);
        setIsRunning(true);
        setStepStartTime(Date.now());
      }
    } catch (error) {
      console.error('Failed to start test session:', error);
    }
  };

  const completeStep = async (success: boolean = true) => {
    if (!session || !stepStartTime) return;

    const completionTime = Date.now() - stepStartTime;

    try {
      await fetch(`/api/user-acceptance/sessions/${session.id}/progress`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step_index: currentStepIndex,
          completion_time: completionTime,
          success
        })
      });

      // Update local state
      const updatedSteps = [...completedSteps];
      updatedSteps[currentStepIndex] = {
        ...updatedSteps[currentStepIndex],
        completed: true,
        startTime: stepStartTime,
        endTime: Date.now()
      };
      setCompletedSteps(updatedSteps);

      // Move to next step or complete test
      if (currentStepIndex < scenario.steps.length - 1) {
        setCurrentStepIndex(currentStepIndex + 1);
        setStepStartTime(Date.now());
      } else {
        setIsRunning(false);
        // Test completed - show feedback form
      }
    } catch (error) {
      console.error('Failed to update step progress:', error);
    }
  };

  const completeTest = async () => {
    if (!session) return;

    try {
      const response = await fetch(`/api/user-acceptance/sessions/${session.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feedback,
          satisfaction
        })
      });

      if (response.ok) {
        const result = await response.json();
        onComplete(result);
      }
    } catch (error) {
      console.error('Failed to complete test session:', error);
    }
  };

  const pauseTest = () => {
    setIsRunning(false);
  };

  const resumeTest = () => {
    setIsRunning(true);
    setStepStartTime(Date.now());
  };

  const cancelTest = () => {
    setIsRunning(false);
    onCancel();
  };

  const progress = ((currentStepIndex + (completedSteps[currentStepIndex]?.completed ? 1 : 0)) / scenario.steps.length) * 100;
  const isCompleted = currentStepIndex >= scenario.steps.length - 1 && completedSteps[currentStepIndex]?.completed;

  if (!session && !isRunning) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            {scenario.name}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-600">{scenario.description}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold mb-2">Test Steps ({scenario.steps.length})</h4>
              <ul className="space-y-1 text-sm">
                {scenario.steps.map((step, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-gray-400">{index + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Success Criteria</h4>
              <ul className="space-y-1 text-sm">
                {scenario.successCriteria.map((criteria, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>{criteria}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            <span>Estimated duration: {scenario.estimatedDuration} minutes</span>
          </div>

          <div className="flex gap-2">
            <Button onClick={startTest} className="flex items-center gap-2">
              <Play className="h-4 w-4" />
              Start Test
            </Button>
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isCompleted) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-600">
            <CheckCircle className="h-5 w-5" />
            Test Completed
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-green-800">
              Congratulations! You have completed all test steps for "{scenario.name}".
            </p>
          </div>

          <div>
            <Label htmlFor="feedback">Please provide your feedback about this test scenario:</Label>
            <Textarea
              id="feedback"
              placeholder="Share your thoughts about the test experience, any issues encountered, or suggestions for improvement..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="mt-2"
              rows={4}
            />
          </div>

          <div>
            <Label>How satisfied were you with this test experience?</Label>
            <RadioGroup value={satisfaction} onValueChange={setSatisfaction} className="mt-2">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="very_dissatisfied" id="very_dissatisfied" />
                <Label htmlFor="very_dissatisfied">Very Dissatisfied</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="dissatisfied" id="dissatisfied" />
                <Label htmlFor="dissatisfied">Dissatisfied</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="neutral" id="neutral" />
                <Label htmlFor="neutral">Neutral</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="satisfied" id="satisfied" />
                <Label htmlFor="satisfied">Satisfied</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="very_satisfied" id="very_satisfied" />
                <Label htmlFor="very_satisfied">Very Satisfied</Label>
              </div>
            </RadioGroup>
          </div>

          <div className="flex gap-2">
            <Button onClick={completeTest} disabled={!satisfaction}>
              Submit Results
            </Button>
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{scenario.name}</span>
          <div className="flex items-center gap-2">
            {isRunning ? (
              <Button variant="outline" size="sm" onClick={pauseTest}>
                <Pause className="h-4 w-4" />
              </Button>
            ) : (
              <Button variant="outline" size="sm" onClick={resumeTest}>
                <Play className="h-4 w-4" />
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={cancelTest}>
              <Square className="h-4 w-4" />
            </Button>
          </div>
        </CardTitle>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Step {currentStepIndex + 1} of {scenario.steps.length}</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <Progress value={progress} className="w-full" />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Current Step */}
        <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
          <h4 className="font-semibold text-blue-900 mb-2">
            Current Step: {scenario.steps[currentStepIndex]}
          </h4>
          {scenario.expectedOutcomes[currentStepIndex] && (
            <p className="text-blue-800 text-sm">
              <strong>Expected outcome:</strong> {scenario.expectedOutcomes[currentStepIndex]}
            </p>
          )}
        </div>

        {/* Step Controls */}
        {isRunning && (
          <div className="flex gap-2">
            <Button onClick={() => completeStep(true)} className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Step Completed Successfully
            </Button>
            <Button 
              variant="outline" 
              onClick={() => completeStep(false)}
              className="flex items-center gap-2"
            >
              <AlertCircle className="h-4 w-4" />
              Step Failed / Skip
            </Button>
          </div>
        )}

        {/* Completed Steps */}
        {completedSteps.some(step => step.completed) && (
          <div>
            <h4 className="font-semibold mb-3">Completed Steps</h4>
            <div className="space-y-2">
              {completedSteps.map((step, index) => (
                step.completed && (
                  <div key={index} className="flex items-center gap-3 p-2 bg-green-50 rounded">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">{step.description}</span>
                    {step.startTime && step.endTime && (
                      <span className="text-xs text-gray-500 ml-auto">
                        {Math.round((step.endTime - step.startTime) / 1000)}s
                      </span>
                    )}
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Remaining Steps */}
        <div>
          <h4 className="font-semibold mb-3">Remaining Steps</h4>
          <div className="space-y-2">
            {scenario.steps.slice(currentStepIndex + 1).map((step, index) => (
              <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                <span className="text-sm text-gray-600">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};