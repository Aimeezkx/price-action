export interface FeedbackData {
  userId?: string;
  sessionId?: string;
  platform: 'web' | 'ios';
  feedbackType: 'bug' | 'feature-request' | 'general' | 'rating';
  category?: string;
  rating?: number; // 1-5 scale
  title?: string;
  description?: string;
  metadata?: any;
}

export interface FeedbackAnalysis {
  overall: any[];
  sentiment: any[];
  categories: any[];
  ratings: any[];
  tags: any[];
}

export interface SentimentScore {
  score: number; // -1 to 1
  label: 'positive' | 'negative' | 'neutral';
}