import AsyncStorage from '@react-native-async-storage/async-storage';
import { Card, Document, Chapter, StudySession, SRSState } from '../types';

export interface OfflineData {
  documents: Document[];
  chapters: Chapter[];
  cards: Card[];
  srsStates: SRSState[];
  studySessions: StudySession[];
  lastSyncTime: string;
}

export interface SyncStatus {
  isOnline: boolean;
  lastSyncTime: Date | null;
  pendingChanges: number;
  syncInProgress: boolean;
}

class OfflineStorageService {
  private readonly STORAGE_KEYS = {
    DOCUMENTS: 'offline_documents',
    CHAPTERS: 'offline_chapters',
    CARDS: 'offline_cards',
    SRS_STATES: 'offline_srs_states',
    STUDY_SESSIONS: 'offline_study_sessions',
    PENDING_CHANGES: 'offline_pending_changes',
    LAST_SYNC: 'offline_last_sync',
    USER_PREFERENCES: 'offline_user_preferences',
  };

  // Document Management
  async saveDocuments(documents: Document[]): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.DOCUMENTS,
        JSON.stringify(documents)
      );
    } catch (error) {
      console.error('Error saving documents offline:', error);
      throw error;
    }
  }

  async getDocuments(): Promise<Document[]> {
    try {
      const documentsJson = await AsyncStorage.getItem(this.STORAGE_KEYS.DOCUMENTS);
      return documentsJson ? JSON.parse(documentsJson) : [];
    } catch (error) {
      console.error('Error loading documents offline:', error);
      return [];
    }
  }

  async saveDocument(document: Document): Promise<void> {
    try {
      const documents = await this.getDocuments();
      const updatedDocuments = documents.filter(d => d.id !== document.id);
      updatedDocuments.push(document);
      await this.saveDocuments(updatedDocuments);
    } catch (error) {
      console.error('Error saving document offline:', error);
      throw error;
    }
  }

  // Chapter Management
  async saveChapters(chapters: Chapter[]): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.CHAPTERS,
        JSON.stringify(chapters)
      );
    } catch (error) {
      console.error('Error saving chapters offline:', error);
      throw error;
    }
  }

  async getChapters(): Promise<Chapter[]> {
    try {
      const chaptersJson = await AsyncStorage.getItem(this.STORAGE_KEYS.CHAPTERS);
      return chaptersJson ? JSON.parse(chaptersJson) : [];
    } catch (error) {
      console.error('Error loading chapters offline:', error);
      return [];
    }
  }

  async getChaptersByDocument(documentId: string): Promise<Chapter[]> {
    try {
      const chapters = await this.getChapters();
      return chapters.filter(chapter => chapter.documentId === documentId);
    } catch (error) {
      console.error('Error loading chapters by document offline:', error);
      return [];
    }
  }

  // Card Management
  async saveCards(cards: Card[]): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.CARDS,
        JSON.stringify(cards)
      );
    } catch (error) {
      console.error('Error saving cards offline:', error);
      throw error;
    }
  }

  async getCards(): Promise<Card[]> {
    try {
      const cardsJson = await AsyncStorage.getItem(this.STORAGE_KEYS.CARDS);
      return cardsJson ? JSON.parse(cardsJson) : [];
    } catch (error) {
      console.error('Error loading cards offline:', error);
      return [];
    }
  }

  async getCardsByChapter(chapterId: string): Promise<Card[]> {
    try {
      const cards = await this.getCards();
      return cards.filter(card => card.chapterId === chapterId);
    } catch (error) {
      console.error('Error loading cards by chapter offline:', error);
      return [];
    }
  }

  async getDueCards(): Promise<Card[]> {
    try {
      const cards = await this.getCards();
      const srsStates = await this.getSRSStates();
      const now = new Date();

      return cards.filter(card => {
        const srsState = srsStates.find(s => s.cardId === card.id);
        if (!srsState) return true; // New cards are due
        return new Date(srsState.dueDate) <= now;
      });
    } catch (error) {
      console.error('Error loading due cards offline:', error);
      return [];
    }
  }

  // SRS State Management
  async saveSRSStates(srsStates: SRSState[]): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.SRS_STATES,
        JSON.stringify(srsStates)
      );
    } catch (error) {
      console.error('Error saving SRS states offline:', error);
      throw error;
    }
  }

  async getSRSStates(): Promise<SRSState[]> {
    try {
      const srsStatesJson = await AsyncStorage.getItem(this.STORAGE_KEYS.SRS_STATES);
      return srsStatesJson ? JSON.parse(srsStatesJson) : [];
    } catch (error) {
      console.error('Error loading SRS states offline:', error);
      return [];
    }
  }

  async updateSRSState(cardId: string, grade: number): Promise<void> {
    try {
      const srsStates = await this.getSRSStates();
      let srsState = srsStates.find(s => s.cardId === cardId);

      if (!srsState) {
        srsState = {
          id: `srs_${cardId}`,
          cardId,
          easeFactor: 2.5,
          interval: 1,
          repetitions: 0,
          dueDate: new Date().toISOString(),
          lastReviewed: new Date().toISOString(),
        };
        srsStates.push(srsState);
      }

      // SM-2 Algorithm implementation
      if (grade >= 3) {
        if (srsState.repetitions === 0) {
          srsState.interval = 1;
        } else if (srsState.repetitions === 1) {
          srsState.interval = 6;
        } else {
          srsState.interval = Math.round(srsState.interval * srsState.easeFactor);
        }
        srsState.repetitions += 1;
      } else {
        srsState.repetitions = 0;
        srsState.interval = 1;
      }

      srsState.easeFactor = Math.max(1.3, srsState.easeFactor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)));
      
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + srsState.interval);
      srsState.dueDate = dueDate.toISOString();
      srsState.lastReviewed = new Date().toISOString();

      await this.saveSRSStates(srsStates);
      await this.addPendingChange('srs_update', { cardId, srsState });
    } catch (error) {
      console.error('Error updating SRS state offline:', error);
      throw error;
    }
  }

  // Study Session Management
  async saveStudySession(session: StudySession): Promise<void> {
    try {
      const sessions = await this.getStudySessions();
      sessions.push(session);
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.STUDY_SESSIONS,
        JSON.stringify(sessions)
      );
      await this.addPendingChange('study_session', session);
    } catch (error) {
      console.error('Error saving study session offline:', error);
      throw error;
    }
  }

  async getStudySessions(): Promise<StudySession[]> {
    try {
      const sessionsJson = await AsyncStorage.getItem(this.STORAGE_KEYS.STUDY_SESSIONS);
      return sessionsJson ? JSON.parse(sessionsJson) : [];
    } catch (error) {
      console.error('Error loading study sessions offline:', error);
      return [];
    }
  }

  // Sync Management
  async addPendingChange(type: string, data: any): Promise<void> {
    try {
      const pendingChanges = await this.getPendingChanges();
      pendingChanges.push({
        id: `${type}_${Date.now()}_${Math.random()}`,
        type,
        data,
        timestamp: new Date().toISOString(),
      });
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.PENDING_CHANGES,
        JSON.stringify(pendingChanges)
      );
    } catch (error) {
      console.error('Error adding pending change:', error);
    }
  }

  async getPendingChanges(): Promise<any[]> {
    try {
      const changesJson = await AsyncStorage.getItem(this.STORAGE_KEYS.PENDING_CHANGES);
      return changesJson ? JSON.parse(changesJson) : [];
    } catch (error) {
      console.error('Error loading pending changes:', error);
      return [];
    }
  }

  async clearPendingChanges(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.STORAGE_KEYS.PENDING_CHANGES);
    } catch (error) {
      console.error('Error clearing pending changes:', error);
    }
  }

  async getLastSyncTime(): Promise<Date | null> {
    try {
      const lastSyncJson = await AsyncStorage.getItem(this.STORAGE_KEYS.LAST_SYNC);
      return lastSyncJson ? new Date(JSON.parse(lastSyncJson)) : null;
    } catch (error) {
      console.error('Error loading last sync time:', error);
      return null;
    }
  }

  async setLastSyncTime(time: Date): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.LAST_SYNC,
        JSON.stringify(time.toISOString())
      );
    } catch (error) {
      console.error('Error saving last sync time:', error);
    }
  }

  // User Preferences
  async saveUserPreferences(preferences: any): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.USER_PREFERENCES,
        JSON.stringify(preferences)
      );
    } catch (error) {
      console.error('Error saving user preferences:', error);
      throw error;
    }
  }

  async getUserPreferences(): Promise<any> {
    try {
      const preferencesJson = await AsyncStorage.getItem(this.STORAGE_KEYS.USER_PREFERENCES);
      return preferencesJson ? JSON.parse(preferencesJson) : {};
    } catch (error) {
      console.error('Error loading user preferences:', error);
      return {};
    }
  }

  // Storage Management
  async getStorageSize(): Promise<number> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      let totalSize = 0;
      
      for (const key of keys) {
        if (key.startsWith('offline_')) {
          const value = await AsyncStorage.getItem(key);
          if (value) {
            totalSize += new Blob([value]).size;
          }
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Error calculating storage size:', error);
      return 0;
    }
  }

  async clearAllOfflineData(): Promise<void> {
    try {
      const keys = Object.values(this.STORAGE_KEYS);
      await AsyncStorage.multiRemove(keys);
    } catch (error) {
      console.error('Error clearing offline data:', error);
      throw error;
    }
  }

  async exportOfflineData(): Promise<OfflineData> {
    try {
      const [documents, chapters, cards, srsStates, studySessions, lastSyncTime] = await Promise.all([
        this.getDocuments(),
        this.getChapters(),
        this.getCards(),
        this.getSRSStates(),
        this.getStudySessions(),
        this.getLastSyncTime(),
      ]);

      return {
        documents,
        chapters,
        cards,
        srsStates,
        studySessions,
        lastSyncTime: lastSyncTime?.toISOString() || new Date().toISOString(),
      };
    } catch (error) {
      console.error('Error exporting offline data:', error);
      throw error;
    }
  }

  async importOfflineData(data: OfflineData): Promise<void> {
    try {
      await Promise.all([
        this.saveDocuments(data.documents),
        this.saveChapters(data.chapters),
        this.saveCards(data.cards),
        this.saveSRSStates(data.srsStates),
        AsyncStorage.setItem(this.STORAGE_KEYS.STUDY_SESSIONS, JSON.stringify(data.studySessions)),
        this.setLastSyncTime(new Date(data.lastSyncTime)),
      ]);
    } catch (error) {
      console.error('Error importing offline data:', error);
      throw error;
    }
  }
}

export const offlineStorage = new OfflineStorageService();