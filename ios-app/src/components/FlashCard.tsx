import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  Image,
} from 'react-native';
import type { Card } from '../types';
import { hapticService } from '../services/hapticService';
import { ImageHotspotViewer } from './ImageHotspotViewer';

interface FlashCardProps {
  card: Card;
  isFlipped: boolean;
  onFlip: () => void;
  style?: any;
}

const { width: screenWidth } = Dimensions.get('window');

export function FlashCard({ card, isFlipped, onFlip, style }: FlashCardProps) {
  const [flipAnimation] = useState(new Animated.Value(0));

  React.useEffect(() => {
    Animated.timing(flipAnimation, {
      toValue: isFlipped ? 1 : 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [isFlipped, flipAnimation]);

  const frontInterpolate = flipAnimation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '180deg'],
  });

  const backInterpolate = flipAnimation.interpolate({
    inputRange: [0, 1],
    outputRange: ['180deg', '360deg'],
  });

  const renderCardContent = (content: string, isBack: boolean = false) => {
    if (card.card_type === 'image_hotspot' && !isBack) {
      const hotspots = card.metadata?.hotspots || [];
      return (
        <View style={styles.imageContainer}>
          <ImageHotspotViewer
            imageSrc={content}
            hotspots={hotspots}
            mode="study"
            onHotspotClick={(hotspot) => {
              console.log('Hotspot clicked:', hotspot.label);
            }}
            onValidationComplete={(correct, clickedHotspots) => {
              console.log('Validation complete:', correct, clickedHotspots.length);
              // Auto-flip card after validation
              setTimeout(() => {
                if (!isFlipped) {
                  handleFlip();
                }
              }, 2500);
            }}
          />
        </View>
      );
    }

    if (card.card_type === 'cloze') {
      const blanks = card.metadata?.blanks || [];
      let displayText = content;
      
      if (!isBack && blanks.length > 0) {
        blanks.forEach((blank: string, index: number) => {
          displayText = displayText.replace(blank, `[${index + 1}]`);
        });
      }

      return (
        <Text style={styles.cardText}>{displayText}</Text>
      );
    }

    return (
      <Text style={styles.cardText}>{content}</Text>
    );
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 1.5) return '#10B981'; // green
    if (difficulty <= 2.5) return '#F59E0B'; // yellow
    return '#EF4444'; // red
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty <= 1.5) return 'Easy';
    if (difficulty <= 2.5) return 'Medium';
    return 'Hard';
  };

  const handleFlip = () => {
    hapticService.cardFlip();
    onFlip();
  };

  return (
    <TouchableOpacity
      style={[styles.container, style]}
      onPress={handleFlip}
      activeOpacity={0.8}
    >
      <View style={styles.cardContainer}>
        {/* Front of card */}
        <Animated.View
          style={[
            styles.card,
            styles.cardFront,
            { transform: [{ rotateY: frontInterpolate }] },
            isFlipped && styles.cardHidden,
          ]}
        >
          <View style={styles.cardHeader}>
            <Text style={styles.cardType}>
              {card.card_type.replace('_', ' ').toUpperCase()}
            </Text>
            <View
              style={[
                styles.difficultyBadge,
                { backgroundColor: getDifficultyColor(card.difficulty) },
              ]}
            >
              <Text style={styles.difficultyText}>
                {getDifficultyLabel(card.difficulty)}
              </Text>
            </View>
          </View>

          <View style={styles.cardContent}>
            {renderCardContent(card.front)}
          </View>

          <View style={styles.cardFooter}>
            <Text style={styles.flipHint}>Tap to flip</Text>
          </View>
        </Animated.View>

        {/* Back of card */}
        <Animated.View
          style={[
            styles.card,
            styles.cardBack,
            { transform: [{ rotateY: backInterpolate }] },
            !isFlipped && styles.cardHidden,
          ]}
        >
          <View style={styles.cardHeader}>
            <Text style={[styles.cardType, styles.answerType]}>ANSWER</Text>
          </View>

          <View style={styles.cardContent}>
            {renderCardContent(card.back, true)}
          </View>

          <View style={styles.cardFooter}>
            <Text style={styles.gradeHint}>Grade your answer</Text>
          </View>
        </Animated.View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    width: screenWidth - 32,
    height: 400,
    alignSelf: 'center',
  },
  cardContainer: {
    flex: 1,
    position: 'relative',
  },
  card: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    backfaceVisibility: 'hidden',
  },
  cardFront: {
    borderColor: '#E5E7EB',
    borderWidth: 1,
  },
  cardBack: {
    backgroundColor: '#EFF6FF',
    borderColor: '#DBEAFE',
    borderWidth: 1,
  },
  cardHidden: {
    opacity: 0,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  cardType: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    letterSpacing: 1,
  },
  answerType: {
    color: '#2563EB',
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  cardContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardText: {
    fontSize: 18,
    lineHeight: 28,
    color: '#1F2937',
    textAlign: 'center',
  },
  imageContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  cardImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
  },
  imageHint: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 12,
    textAlign: 'center',
  },
  cardFooter: {
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  flipHint: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  gradeHint: {
    fontSize: 12,
    color: '#60A5FA',
  },
});