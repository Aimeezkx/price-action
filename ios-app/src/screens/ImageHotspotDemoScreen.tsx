import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { ImageHotspotViewer } from '../components/ImageHotspotViewer';
import type { Hotspot } from '../types';

const sampleHotspots: Hotspot[] = [
  {
    id: '1',
    x: 25,
    y: 30,
    width: 15,
    height: 20,
    label: 'Heart',
    description: 'The heart pumps blood throughout the body',
    correct: true,
  },
  {
    id: '2',
    x: 60,
    y: 25,
    width: 12,
    height: 15,
    label: 'Lungs',
    description: 'The lungs are responsible for breathing',
    correct: true,
  },
  {
    id: '3',
    x: 45,
    y: 60,
    width: 10,
    height: 12,
    label: 'Stomach',
    description: 'The stomach digests food',
    correct: false,
  },
  {
    id: '4',
    x: 35,
    y: 15,
    width: 8,
    height: 10,
    label: 'Brain',
    description: 'The brain controls the nervous system',
    correct: true,
  },
];

export function ImageHotspotDemoScreen() {
  const [mode, setMode] = useState<'study' | 'answer'>('study');
  const [results, setResults] = useState<string>('');

  const handleHotspotClick = (hotspot: Hotspot) => {
    console.log('Hotspot clicked:', hotspot.label);
  };

  const handleValidationComplete = (correct: boolean, clickedHotspots: Hotspot[]) => {
    const resultText = `Validation complete!\nCorrect: ${correct}\nClicked: ${clickedHotspots.map(h => h.label).join(', ')}`;
    setResults(resultText);
    console.log('Validation complete:', correct, clickedHotspots);
  };

  const toggleMode = () => {
    setMode(prev => prev === 'study' ? 'answer' : 'study');
    setResults('');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>Image Hotspot Demo</Text>
          <TouchableOpacity
            style={[
              styles.modeButton,
              mode === 'study' ? styles.studyMode : styles.answerMode
            ]}
            onPress={toggleMode}
          >
            <Text style={styles.modeButtonText}>
              Mode: {mode.toUpperCase()}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.instructions}>
          <Text style={styles.instructionsTitle}>Instructions:</Text>
          <Text style={styles.instructionsText}>
            {mode === 'study' 
              ? '• Tap on the anatomical structures\n• Find all 3 correct areas\n• Pinch to zoom, drag to pan\n• Double tap to reset zoom'
              : '• View mode showing all hotspots\n• Green = correct areas\n• Red = incorrect areas'
            }
          </Text>
        </View>

        <View style={styles.imageContainer}>
          <ImageHotspotViewer
            imageSrc="https://via.placeholder.com/400x300/E5E7EB/6B7280?text=Sample+Anatomy+Image"
            hotspots={sampleHotspots}
            mode={mode}
            onHotspotClick={handleHotspotClick}
            onValidationComplete={handleValidationComplete}
            maxZoom={3}
            minZoom={0.5}
          />
        </View>

        {results ? (
          <View style={styles.results}>
            <Text style={styles.resultsTitle}>Results:</Text>
            <Text style={styles.resultsText}>{results}</Text>
          </View>
        ) : null}

        <View style={styles.hotspotList}>
          <Text style={styles.hotspotListTitle}>Available Hotspots:</Text>
          {sampleHotspots.map((hotspot, index) => (
            <View key={hotspot.id} style={styles.hotspotItem}>
              <View style={[
                styles.hotspotIndicator,
                hotspot.correct ? styles.correctIndicator : styles.incorrectIndicator
              ]} />
              <View style={styles.hotspotInfo}>
                <Text style={styles.hotspotLabel}>{hotspot.label}</Text>
                <Text style={styles.hotspotDescription}>{hotspot.description}</Text>
                <Text style={styles.hotspotStatus}>
                  {hotspot.correct ? 'Correct answer' : 'Incorrect option'}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1F2937',
  },
  modeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  studyMode: {
    backgroundColor: '#3B82F6',
  },
  answerMode: {
    backgroundColor: '#10B981',
  },
  modeButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  instructions: {
    backgroundColor: '#FFFFFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  instructionsText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  imageContainer: {
    backgroundColor: '#FFFFFF',
    margin: 16,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
    height: 400,
  },
  results: {
    backgroundColor: '#FFFFFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  resultsText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  hotspotList: {
    backgroundColor: '#FFFFFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  hotspotListTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 12,
  },
  hotspotItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  hotspotIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 2,
    marginRight: 12,
  },
  correctIndicator: {
    backgroundColor: '#10B981',
  },
  incorrectIndicator: {
    backgroundColor: '#EF4444',
  },
  hotspotInfo: {
    flex: 1,
  },
  hotspotLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 2,
  },
  hotspotDescription: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 2,
  },
  hotspotStatus: {
    fontSize: 12,
    color: '#9CA3AF',
    fontStyle: 'italic',
  },
});