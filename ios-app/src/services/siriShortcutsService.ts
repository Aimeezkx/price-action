import { NativeModules, Platform } from 'react-native';
import { offlineStorage } from './offlineStorage';

export interface SiriShortcut {
  identifier: string;
  title: string;
  subtitle?: string;
  phrase: string;
  isEligibleForSearch: boolean;
  isEligibleForPrediction: boolean;
  parameters?: Record<string, any>;
}

export interface VoiceCommand {
  command: string;
  parameters: Record<string, any>;
  confidence: number;
}

class SiriShortcutsService {
  private shortcuts: SiriShortcut[] = [
    {
      identifier: 'start-study-session',
      title: 'Start Study Session',
      subtitle: 'Begin reviewing flashcards',
      phrase: 'Start studying',
      isEligibleForSearch: true,
      isEligibleForPrediction: true,
    },
    {
      identifier: 'quick-review',
      title: 'Quick Review',
      subtitle: 'Review 5 cards quickly',
      phrase: 'Quick review',
      isEligibleForSearch: true,
      isEligibleForPrediction: true,
      parameters: { cardCount: 5 },
    },
    {
      identifier: 'check-due-cards',
      title: 'Check Due Cards',
      subtitle: 'See how many cards are due for review',
      phrase: 'How many cards are due',
      isEligibleForSearch: true,
      isEligibleForPrediction: true,
    },
    {
      identifier: 'study-specific-chapter',
      title: 'Study Chapter',
      subtitle: 'Study cards from a specific chapter',
      phrase: 'Study chapter',
      isEligibleForSearch: true,
      isEligibleForPrediction: false,
    },
    {
      identifier: 'view-study-stats',
      title: 'View Study Stats',
      subtitle: 'Check your study progress and statistics',
      phrase: 'Show my study progress',
      isEligibleForSearch: true,
      isEligibleForPrediction: true,
    },
    {
      identifier: 'schedule-study-reminder',
      title: 'Schedule Study Reminder',
      subtitle: 'Set a reminder for your next study session',
      phrase: 'Remind me to study',
      isEligibleForSearch: true,
      isEligibleForPrediction: false,
    },
  ];

  async initializeSiriShortcuts(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      for (const shortcut of this.shortcuts) {
        await this.donateShortcut(shortcut);
      }
    } catch (error) {
      console.error('Error initializing Siri shortcuts:', error);
    }
  }

  async donateShortcut(shortcut: SiriShortcut): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      if (NativeModules.SiriShortcutsManager) {
        await NativeModules.SiriShortcutsManager.donateShortcut({
          identifier: shortcut.identifier,
          title: shortcut.title,
          subtitle: shortcut.subtitle,
          phrase: shortcut.phrase,
          isEligibleForSearch: shortcut.isEligibleForSearch,
          isEligibleForPrediction: shortcut.isEligibleForPrediction,
          userInfo: shortcut.parameters || {},
        });
      }
    } catch (error) {
      console.error('Error donating Siri shortcut:', error);
    }
  }

  async handleSiriShortcut(identifier: string, parameters?: Record<string, any>): Promise<any> {
    try {
      switch (identifier) {
        case 'start-study-session':
          return await this.handleStartStudySession();
        
        case 'quick-review':
          return await this.handleQuickReview(parameters?.cardCount || 5);
        
        case 'check-due-cards':
          return await this.handleCheckDueCards();
        
        case 'study-specific-chapter':
          return await this.handleStudySpecificChapter(parameters?.chapterId);
        
        case 'view-study-stats':
          return await this.handleViewStudyStats();
        
        case 'schedule-study-reminder':
          return await this.handleScheduleStudyReminder(parameters);
        
        default:
          console.log('Unknown Siri shortcut:', identifier);
          return { success: false, message: 'Unknown command' };
      }
    } catch (error) {
      console.error('Error handling Siri shortcut:', error);
      return { success: false, message: 'Error processing command' };
    }
  }

  private async handleStartStudySession(): Promise<any> {
    try {
      const dueCards = await offlineStorage.getDueCards();
      
      if (dueCards.length === 0) {
        return {
          success: true,
          message: 'No cards are due for review right now. Great job staying on top of your studies!',
          action: 'show_message',
        };
      }

      return {
        success: true,
        message: `Starting study session with ${dueCards.length} cards`,
        action: 'navigate_to_study',
        data: { cards: dueCards },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Unable to start study session',
      };
    }
  }

  private async handleQuickReview(cardCount: number): Promise<any> {
    try {
      const dueCards = await offlineStorage.getDueCards();
      const reviewCards = dueCards.slice(0, cardCount);

      if (reviewCards.length === 0) {
        return {
          success: true,
          message: 'No cards are due for review right now.',
          action: 'show_message',
        };
      }

      return {
        success: true,
        message: `Starting quick review with ${reviewCards.length} cards`,
        action: 'navigate_to_study',
        data: { cards: reviewCards, isQuickReview: true },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Unable to start quick review',
      };
    }
  }

  private async handleCheckDueCards(): Promise<any> {
    try {
      const dueCards = await offlineStorage.getDueCards();
      const message = dueCards.length === 0 
        ? 'You have no cards due for review. Well done!'
        : `You have ${dueCards.length} card${dueCards.length === 1 ? '' : 's'} due for review.`;

      return {
        success: true,
        message,
        action: 'show_message',
        data: { dueCount: dueCards.length },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Unable to check due cards',
      };
    }
  }

  private async handleStudySpecificChapter(chapterId?: string): Promise<any> {
    try {
      if (!chapterId) {
        const chapters = await offlineStorage.getChapters();
        return {
          success: true,
          message: 'Which chapter would you like to study?',
          action: 'show_chapter_selection',
          data: { chapters },
        };
      }

      const cards = await offlineStorage.getCardsByChapter(chapterId);
      const dueCards = cards.filter(async card => {
        const srsStates = await offlineStorage.getSRSStates();
        const srsState = srsStates.find(s => s.cardId === card.id);
        if (!srsState) return true;
        return new Date(srsState.dueDate) <= new Date();
      });

      return {
        success: true,
        message: `Starting chapter study with ${dueCards.length} cards`,
        action: 'navigate_to_study',
        data: { cards: dueCards, chapterId },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Unable to start chapter study',
      };
    }
  }

  private async handleViewStudyStats(): Promise<any> {
    try {
      const [allCards, dueCards, studySessions] = await Promise.all([
        offlineStorage.getCards(),
        offlineStorage.getDueCards(),
        offlineStorage.getStudySessions(),
      ]);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const todayReviewed = studySessions.filter(session => {
        const sessionDate = new Date(session.startTime);
        sessionDate.setHours(0, 0, 0, 0);
        return sessionDate.getTime() === today.getTime();
      }).reduce((total, session) => total + session.cardsReviewed, 0);

      const message = `You have ${allCards.length} total cards, ${dueCards.length} due for review, and you've reviewed ${todayReviewed} cards today.`;

      return {
        success: true,
        message,
        action: 'show_stats',
        data: {
          totalCards: allCards.length,
          dueCards: dueCards.length,
          reviewedToday: todayReviewed,
        },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Unable to retrieve study statistics',
      };
    }
  }

  private async handleScheduleStudyReminder(parameters?: Record<string, any>): Promise<any> {
    try {
      // This would integrate with the notification service
      const defaultTime = parameters?.time || '19:00'; // 7 PM default
      
      return {
        success: true,
        message: `Study reminder scheduled for ${defaultTime}`,
        action: 'schedule_notification',
        data: { time: defaultTime },
      };
    } catch (error) {
      return {
        success: false,
        message: 'Unable to schedule study reminder',
      };
    }
  }

  async updateShortcutPredictions(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      const dueCards = await offlineStorage.getDueCards();
      const studySessions = await offlineStorage.getStudySessions();

      // Update prediction relevance based on user behavior
      const recentSessions = studySessions.slice(-10);
      const hasRecentActivity = recentSessions.length > 0;
      const hasDueCards = dueCards.length > 0;

      // Donate shortcuts with updated relevance
      if (hasDueCards) {
        await this.donateShortcut({
          ...this.shortcuts.find(s => s.identifier === 'start-study-session')!,
          isEligibleForPrediction: true,
        });
      }

      if (hasRecentActivity) {
        await this.donateShortcut({
          ...this.shortcuts.find(s => s.identifier === 'view-study-stats')!,
          isEligibleForPrediction: true,
        });
      }
    } catch (error) {
      console.error('Error updating shortcut predictions:', error);
    }
  }

  async removeAllShortcuts(): Promise<void> {
    if (Platform.OS !== 'ios') return;

    try {
      if (NativeModules.SiriShortcutsManager) {
        await NativeModules.SiriShortcutsManager.removeAllShortcuts();
      }
    } catch (error) {
      console.error('Error removing Siri shortcuts:', error);
    }
  }

  async getAvailableShortcuts(): Promise<SiriShortcut[]> {
    return this.shortcuts;
  }

  async processVoiceCommand(command: string): Promise<any> {
    const normalizedCommand = command.toLowerCase().trim();
    
    // Simple command matching - in a real app, you'd use more sophisticated NLP
    if (normalizedCommand.includes('start study') || normalizedCommand.includes('begin study')) {
      return await this.handleSiriShortcut('start-study-session');
    }
    
    if (normalizedCommand.includes('quick review')) {
      return await this.handleSiriShortcut('quick-review');
    }
    
    if (normalizedCommand.includes('how many') && normalizedCommand.includes('due')) {
      return await this.handleSiriShortcut('check-due-cards');
    }
    
    if (normalizedCommand.includes('study progress') || normalizedCommand.includes('stats')) {
      return await this.handleSiriShortcut('view-study-stats');
    }
    
    return {
      success: false,
      message: 'Sorry, I didn\'t understand that command. Try saying "Start studying" or "How many cards are due".',
    };
  }
}

export const siriShortcutsService = new SiriShortcutsService();