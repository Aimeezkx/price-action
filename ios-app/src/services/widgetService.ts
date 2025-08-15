import { NativeModules, Platform } from 'react-native';
import { offlineStorage } from './offlineStorage';

export interface WidgetData {
  dueCardsCount: number;
  studyStreak: number;
  todayReviewed: number;
  totalCards: number;
  nextReviewTime: string | null;
  progressPercentage: number;
}

export interface StudyStats {
  totalCards: number;
  dueCards: number;
  reviewedToday: number;
  studyStreak: number;
  averageGrade: number;
  weeklyProgress: number[];
}

class WidgetService {
  private readonly WIDGET_IDENTIFIER = 'com.documentlearning.studywidget';

  async updateStudyProgressWidget(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      const widgetData = await this.getWidgetData();
      
      // Update widget using native module (would need to be implemented in native iOS code)
      if (NativeModules.WidgetManager) {
        await NativeModules.WidgetManager.updateWidget(
          this.WIDGET_IDENTIFIER,
          widgetData
        );
      }
    } catch (error) {
      console.error('Error updating study progress widget:', error);
    }
  }

  async getWidgetData(): Promise<WidgetData> {
    try {
      const [dueCards, allCards, studySessions] = await Promise.all([
        offlineStorage.getDueCards(),
        offlineStorage.getCards(),
        offlineStorage.getStudySessions(),
      ]);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const todayReviewed = studySessions.filter(session => {
        const sessionDate = new Date(session.startTime);
        sessionDate.setHours(0, 0, 0, 0);
        return sessionDate.getTime() === today.getTime();
      }).reduce((total, session) => total + session.cardsReviewed, 0);

      const studyStreak = await this.calculateStudyStreak();
      const nextReviewTime = await this.getNextReviewTime();
      const progressPercentage = allCards.length > 0 
        ? Math.round(((allCards.length - dueCards.length) / allCards.length) * 100)
        : 0;

      return {
        dueCardsCount: dueCards.length,
        studyStreak,
        todayReviewed,
        totalCards: allCards.length,
        nextReviewTime,
        progressPercentage,
      };
    } catch (error) {
      console.error('Error getting widget data:', error);
      return {
        dueCardsCount: 0,
        studyStreak: 0,
        todayReviewed: 0,
        totalCards: 0,
        nextReviewTime: null,
        progressPercentage: 0,
      };
    }
  }

  async getStudyStats(): Promise<StudyStats> {
    try {
      const [allCards, dueCards, studySessions, srsStates] = await Promise.all([
        offlineStorage.getCards(),
        offlineStorage.getDueCards(),
        offlineStorage.getStudySessions(),
        offlineStorage.getSRSStates(),
      ]);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const todayReviewed = studySessions.filter(session => {
        const sessionDate = new Date(session.startTime);
        sessionDate.setHours(0, 0, 0, 0);
        return sessionDate.getTime() === today.getTime();
      }).reduce((total, session) => total + session.cardsReviewed, 0);

      const studyStreak = await this.calculateStudyStreak();

      // Calculate average grade from recent sessions
      const recentSessions = studySessions.slice(-10);
      const totalGrades = recentSessions.reduce((sum, session) => sum + (session.averageGrade || 0), 0);
      const averageGrade = recentSessions.length > 0 ? totalGrades / recentSessions.length : 0;

      // Calculate weekly progress (last 7 days)
      const weeklyProgress = await this.getWeeklyProgress();

      return {
        totalCards: allCards.length,
        dueCards: dueCards.length,
        reviewedToday: todayReviewed,
        studyStreak,
        averageGrade,
        weeklyProgress,
      };
    } catch (error) {
      console.error('Error getting study stats:', error);
      return {
        totalCards: 0,
        dueCards: 0,
        reviewedToday: 0,
        studyStreak: 0,
        averageGrade: 0,
        weeklyProgress: [0, 0, 0, 0, 0, 0, 0],
      };
    }
  }

  private async calculateStudyStreak(): Promise<number> {
    try {
      const studySessions = await offlineStorage.getStudySessions();
      if (studySessions.length === 0) return 0;

      // Sort sessions by date (newest first)
      const sortedSessions = studySessions.sort((a, b) => 
        new Date(b.startTime).getTime() - new Date(a.startTime).getTime()
      );

      let streak = 0;
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      // Group sessions by date
      const sessionsByDate = new Map<string, boolean>();
      sortedSessions.forEach(session => {
        const sessionDate = new Date(session.startTime);
        sessionDate.setHours(0, 0, 0, 0);
        const dateKey = sessionDate.toISOString().split('T')[0];
        sessionsByDate.set(dateKey, true);
      });

      // Check consecutive days starting from today
      let currentDate = new Date(today);
      while (true) {
        const dateKey = currentDate.toISOString().split('T')[0];
        if (sessionsByDate.has(dateKey)) {
          streak++;
          currentDate.setDate(currentDate.getDate() - 1);
        } else {
          break;
        }
      }

      return streak;
    } catch (error) {
      console.error('Error calculating study streak:', error);
      return 0;
    }
  }

  private async getNextReviewTime(): Promise<string | null> {
    try {
      const srsStates = await offlineStorage.getSRSStates();
      if (srsStates.length === 0) return null;

      // Find the earliest due date
      const nextDue = srsStates
        .map(state => new Date(state.dueDate))
        .sort((a, b) => a.getTime() - b.getTime())[0];

      return nextDue ? nextDue.toISOString() : null;
    } catch (error) {
      console.error('Error getting next review time:', error);
      return null;
    }
  }

  private async getWeeklyProgress(): Promise<number[]> {
    try {
      const studySessions = await offlineStorage.getStudySessions();
      const weeklyProgress = new Array(7).fill(0);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        
        const dayProgress = studySessions.filter(session => {
          const sessionDate = new Date(session.startTime);
          sessionDate.setHours(0, 0, 0, 0);
          return sessionDate.getTime() === date.getTime();
        }).reduce((total, session) => total + session.cardsReviewed, 0);

        weeklyProgress[6 - i] = dayProgress;
      }

      return weeklyProgress;
    } catch (error) {
      console.error('Error getting weekly progress:', error);
      return [0, 0, 0, 0, 0, 0, 0];
    }
  }

  async scheduleWidgetUpdates(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      // Schedule widget updates using background tasks
      if (NativeModules.WidgetManager) {
        await NativeModules.WidgetManager.scheduleUpdates(this.WIDGET_IDENTIFIER);
      }
    } catch (error) {
      console.error('Error scheduling widget updates:', error);
    }
  }

  async createStudyProgressWidget(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      const widgetData = await this.getWidgetData();
      
      if (NativeModules.WidgetManager) {
        await NativeModules.WidgetManager.createWidget({
          identifier: this.WIDGET_IDENTIFIER,
          displayName: 'Study Progress',
          description: 'Track your daily study progress and due cards',
          data: widgetData,
        });
      }
    } catch (error) {
      console.error('Error creating study progress widget:', error);
    }
  }

  async removeStudyProgressWidget(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      if (NativeModules.WidgetManager) {
        await NativeModules.WidgetManager.removeWidget(this.WIDGET_IDENTIFIER);
      }
    } catch (error) {
      console.error('Error removing study progress widget:', error);
    }
  }

  // Widget interaction handlers
  async handleWidgetTap(action: string): Promise<void> {
    switch (action) {
      case 'start_study':
        // Navigate to study screen
        // This would be handled by the navigation system
        break;
      case 'view_progress':
        // Navigate to progress screen
        break;
      case 'quick_review':
        // Start a quick review session
        break;
      default:
        console.log('Unknown widget action:', action);
    }
  }
}

export const widgetService = new WidgetService();