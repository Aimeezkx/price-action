import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { hapticService } from '../services/hapticService';

interface GradingInterfaceProps {
  onGrade: (grade: number) => void;
  disabled?: boolean;
  style?: any;
}

const { width: screenWidth } = Dimensions.get('window');

const gradeOptions = [
  { value: 0, label: 'Again', description: 'Complete blackout', color: '#EF4444' },
  { value: 1, label: 'Hard', description: 'Incorrect, but remembered', color: '#F97316' },
  { value: 2, label: 'Good', description: 'Correct with hesitation', color: '#EAB308' },
  { value: 3, label: 'Easy', description: 'Correct with some thought', color: '#22C55E' },
  { value: 4, label: 'Perfect', description: 'Correct immediately', color: '#3B82F6' },
  { value: 5, label: 'Too Easy', description: 'Trivially easy', color: '#8B5CF6' },
];

export function GradingInterface({ onGrade, disabled = false, style }: GradingInterfaceProps) {
  const handleGrade = (grade: number) => {
    hapticService.cardGrade(grade);
    onGrade(grade);
  };

  return (
    <View style={[styles.container, style]}>
      <View style={styles.header}>
        <Text style={styles.title}>How well did you know this?</Text>
        <Text style={styles.subtitle}>Tap a button to grade your answer</Text>
      </View>

      <View style={styles.gradeGrid}>
        {gradeOptions.map((option) => (
          <TouchableOpacity
            key={option.value}
            style={[
              styles.gradeButton,
              { backgroundColor: option.color },
              disabled && styles.gradeButtonDisabled,
            ]}
            onPress={() => handleGrade(option.value)}
            disabled={disabled}
            activeOpacity={0.8}
          >
            <Text style={styles.gradeValue}>{option.value}</Text>
            <Text style={styles.gradeLabel}>{option.label}</Text>
            <Text style={styles.gradeDescription}>{option.description}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Tap the card to flip • Use the buttons above to grade
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: screenWidth - 32,
    alignSelf: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  gradeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  gradeButton: {
    width: (screenWidth - 96) / 3, // 3 buttons per row with margins
    height: 80,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  gradeButtonDisabled: {
    opacity: 0.5,
  },
  gradeValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  gradeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  gradeDescription: {
    fontSize: 10,
    color: '#FFFFFF',
    opacity: 0.9,
    textAlign: 'center',
  },
  footer: {
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  footerText: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});