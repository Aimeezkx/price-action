import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Alert,
  Dimensions,
  ScrollView,
} from 'react-native';
import { FlashCard } from '../components/FlashCard';
import { GradingInterface } from '../components/GradingInterface';
import { useTodayReview, useGradeCard } from '../hooks/useCards';
import { hapticService } from '../services/hapticService';
import { offlineStorage } from '../services/offlineStorage';
import { notificationService } from '../services/notificationService';
import { widgetService } from '../services/widgetService';
import type { Card } from '../types';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export function StudyScreen() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [reviewedCards, setReviewedCards] = useState<Set<string>>(new Set());
  const [sessionStats, setSessionStats] = useState({
    total: 0,
    reviewed: 0,
    correct: 0,
    startTime: Date.now(),
  });

  const { data: cards, isLoading, error, refetch } = useTodayReview();
  const gradeCardMutation = useGradeCard();

  const currentCard = cards?.[currentIndex];
  const isLastCard = currentIndex === (cards?.length || 0) - 1;

  useEffect(() => {
    if (cards) {
      setSessionStats(prev => ({ ...prev, total: cards.length }));
    }
  }, [cards]);

  const handleFlip = () => {
    if (!gradeCardMutation.isPending) {
      hapticService.cardFlip();
      setIsFlipped(!isFlipped);
    }
  };

  const handleGrade = async (grade: number) => {
    if (!currentCard || gradeCardMutation.isPending) return;

    try {
      // Haptic feedback for grading
      hapticService.cardGrade(grade);
      
      await gradeCardMutation.mutateAsync({ cardId: currentCard.id, grade });
      
      // Update offline storage
      await offlineStorage.updateSRSState(currentCard.id, grade);
      
      // Update stats
      const wasCorrect = grade >= 3;
      setReviewedCards(prev => new Set([...prev, currentCard.id]));
      setSessionStats(prev => ({
        ...prev,
        reviewed: prev.reviewed + 1,
        correct: prev.correct + (wasCorrect ? 1 : 0),
      }));

      // Move to next card or complete session
      if (isLastCard) {
        handleSessionComplete();
      } else {
        setCurrentIndex(currentIndex + 1);
        setIsFlipped(false);
      }
    } catch (error) {
      hapticService.error();
      Alert.alert('Error', 'Failed to save your grade. Please try again.');
    }
  };

  const handleSessionComplete = async () => {
    const accuracy = Math.round((sessionStats.correct / sessionStats.reviewed) * 100);
    const sessionDuration = Date.now() - sessionStats.startTime;
    
    // Haptic feedback for session completion
    hapticService.sessionComplete();
    
    // Save study session to offline storage
    try {
      await offlineStorage.saveStudySession({
        id: `session_${Date.now()}`,
        startTime: new Date(sessionStats.startTime).toISOString(),
        endTime: new Date().toISOString(),
        cardsReviewed: sessionStats.reviewed,
        averageGrade: sessionStats.correct / sessionStats.reviewed * 5,
        accuracy: accuracy / 100,
        duration: sessionDuration,
      });
      
      // Update widget
      await widgetService.updateStudyProgressWidget();
      
      // Schedule next review notification if needed
      const dueCards = await offlineStorage.getDueCards();
      if (dueCards.length > 0) {
        const nextReviewTime = new Date();
        nextReviewTime.setHours(nextReviewTime.getHours() + 4); // 4 hours later
        await notificationService.scheduleReviewReminder(dueCards.length, nextReviewTime);
      }
    } catch (error) {
      console.error('Error saving session data:', error);
    }
    
    Alert.alert(
      'Session Complete!',
      `Great job! You reviewed ${sessionStats.reviewed} cards with ${accuracy}% accuracy.`,
      [
        {
          text: 'Review Again',
          onPress: () => {
            setCurrentIndex(0);
            setIsFlipped(false);
            setReviewedCards(new Set());
            setSessionStats({
              total: cards?.length || 0,
              reviewed: 0,
              correct: 0,
              startTime: Date.now(),
            });
          },
        },
        {
          text: 'Done',
          style: 'default',
        },
      ]
    );
  };

  const handleNavigation = (direction: 'prev' | 'next') => {
    if (gradeCardMutation.isPending) return;

    hapticService.buttonPress();
    
    if (direction === 'prev' && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    } else if (direction === 'next' && currentIndex < (cards?.length || 0) - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const getProgressPercentage = () => {
    if (sessionStats.total === 0) return 0;
    return Math.round((sessionStats.reviewed / sessionStats.total) * 100);
  };

  const getAccuracyPercentage = () => {
    if (sessionStats.reviewed === 0) return 0;
    return Math.round((sessionStats.correct / sessionStats.reviewed) * 100);
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.loadingText}>Loading your cards...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>Failed to load cards</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (!cards || cards.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.noCardsTitle}>No cards due today</Text>
          <Text style={styles.noCardsSubtitle}>
            Great job! You're all caught up with your reviews.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!currentCard) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>No card available</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Review Session</Text>
          <Text style={styles.cardCounter}>
            Card {currentIndex + 1} of {cards.length}
          </Text>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${getProgressPercentage()}%` },
              ]}
            />
          </View>
        </View>

        {/* Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{getProgressPercentage()}%</Text>
            <Text style={styles.statLabel}>Progress</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{getAccuracyPercentage()}%</Text>
            <Text style={styles.statLabel}>Accuracy</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{sessionStats.reviewed}</Text>
            <Text style={styles.statLabel}>Reviewed</Text>
          </View>
        </View>

        {/* Navigation */}
        <View style={styles.navigationContainer}>
          <TouchableOpacity
            style={[
              styles.navButton,
              currentIndex === 0 && styles.navButtonDisabled,
            ]}
            onPress={() => handleNavigation('prev')}
            disabled={currentIndex === 0 || gradeCardMutation.isPending}
          >
            <Text style={styles.navButtonText}>← Previous</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.navButton,
              isLastCard && styles.navButtonDisabled,
            ]}
            onPress={() => handleNavigation('next')}
            disabled={isLastCard || gradeCardMutation.isPending}
          >
            <Text style={styles.navButtonText}>Next →</Text>
          </TouchableOpacity>
        </View>

        {/* Flash Card */}
        <View style={styles.cardContainer}>
          <FlashCard
            card={currentCard}
            isFlipped={isFlipped}
            onFlip={handleFlip}
          />
        </View>

        {/* Grading Interface - Only show when card is flipped */}
        {isFlipped && (
          <View style={styles.gradingContainer}>
            <GradingInterface
              onGrade={handleGrade}
              disabled={gradeCardMutation.isPending}
            />
          </View>
        )}

        {/* Loading indicator */}
        {gradeCardMutation.isPending && (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Saving your grade...</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollContent: {
    paddingBottom: 20,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 4,
  },
  cardCounter: {
    fontSize: 14,
    color: '#6B7280',
  },
  progressContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 80,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  navButton: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  navButtonDisabled: {
    opacity: 0.5,
  },
  navButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  cardContainer: {
    marginBottom: 20,
  },
  gradingContainer: {
    marginBottom: 20,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  noCardsTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  noCardsSubtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
  },
});