import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  ScrollView,
  Alert,
  Switch,
  Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { iOSIntegrationService } from '../services/iOSIntegrationService';
import { hapticService } from '../services/hapticService';
import { offlineStorage } from '../services/offlineStorage';

export function ProfileScreen() {
  const [iOSFeatures, setiOSFeatures] = useState({
    notifications: true,
    widgets: true,
    siriShortcuts: true,
    hapticFeedback: true,
    offlineMode: true,
  });
  const [studyStats, setStudyStats] = useState({
    cardsStudied: 0,
    dayStreak: 0,
    accuracy: 0,
  });

  useEffect(() => {
    loadSettings();
    loadStudyStats();
  }, []);

  const loadSettings = async () => {
    if (Platform.OS === 'ios') {
      try {
        const config = iOSIntegrationService.getFeatureConfig();
        setiOSFeatures(config);
      } catch (error) {
        console.error('Error loading iOS settings:', error);
      }
    }
  };

  const loadStudyStats = async () => {
    try {
      const stats = await iOSIntegrationService.getStudyStats();
      setStudyStats({
        cardsStudied: stats.totalCards,
        dayStreak: stats.studyStreak,
        accuracy: Math.round(stats.averageGrade * 20), // Convert 0-5 scale to percentage
      });
    } catch (error) {
      console.error('Error loading study stats:', error);
    }
  };
  const handleExportData = () => {
    hapticService.buttonPress();
    Alert.alert(
      'Export Data',
      'Choose export format:',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Anki Format', onPress: () => exportData('anki') },
        { text: 'Notion Format', onPress: () => exportData('notion') },
        { text: 'Offline Backup', onPress: () => exportOfflineData() },
      ]
    );
  };

  const exportData = async (format: 'anki' | 'notion') => {
    try {
      // Implementation would call the export API
      hapticService.trigger('notificationSuccess');
      Alert.alert('Success', `Data exported in ${format} format`);
    } catch (error) {
      hapticService.error();
      Alert.alert('Error', 'Failed to export data');
    }
  };

  const exportOfflineData = async () => {
    try {
      const data = await iOSIntegrationService.exportOfflineData();
      // In a real app, this would save to Files app or share
      hapticService.trigger('notificationSuccess');
      Alert.alert('Success', 'Offline data exported successfully');
    } catch (error) {
      hapticService.error();
      Alert.alert('Error', 'Failed to export offline data');
    }
  };

  const handleClearCache = async () => {
    hapticService.buttonPress();
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.clear();
              await offlineStorage.clearAllOfflineData();
              hapticService.trigger('notificationSuccess');
              Alert.alert('Success', 'Cache cleared successfully');
              loadStudyStats(); // Refresh stats
            } catch (error) {
              hapticService.error();
              Alert.alert('Error', 'Failed to clear cache');
            }
          },
        },
      ]
    );
  };

  const toggleiOSFeature = async (feature: keyof typeof iOSFeatures) => {
    if (Platform.OS !== 'ios') return;

    hapticService.buttonPress();
    const newValue = !iOSFeatures[feature];
    
    try {
      if (newValue) {
        await iOSIntegrationService.enableFeature(feature);
      } else {
        await iOSIntegrationService.disableFeature(feature);
      }
      
      setiOSFeatures(prev => ({ ...prev, [feature]: newValue }));
      hapticService.trigger('notificationSuccess');
    } catch (error) {
      hapticService.error();
      Alert.alert('Error', `Failed to ${newValue ? 'enable' : 'disable'} ${feature}`);
    }
  };

  const handleScheduleReminder = () => {
    hapticService.buttonPress();
    Alert.alert(
      'Study Reminder',
      'Set your daily study reminder time:',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: '9:00 AM', onPress: () => scheduleReminder(9, 0) },
        { text: '1:00 PM', onPress: () => scheduleReminder(13, 0) },
        { text: '7:00 PM', onPress: () => scheduleReminder(19, 0) },
      ]
    );
  };

  const scheduleReminder = async (hour: number, minute: number) => {
    try {
      await iOSIntegrationService.scheduleStudyReminder({ hour, minute });
      hapticService.trigger('notificationSuccess');
      Alert.alert('Success', `Daily reminder set for ${hour}:${minute.toString().padStart(2, '0')}`);
    } catch (error) {
      hapticService.error();
      Alert.alert('Error', 'Failed to schedule reminder');
    }
  };

  const settingsOptions = [
    {
      title: 'Study Settings',
      items: [
        { label: 'Daily Review Goal', value: '20 cards', onPress: () => {} },
        { label: 'Schedule Reminder', value: '', onPress: handleScheduleReminder },
        { label: 'Study Streak', value: `${studyStats.dayStreak} days`, onPress: () => {} },
      ],
    },
    ...(Platform.OS === 'ios' ? [{
      title: 'iOS Features',
      items: [
        { 
          label: 'Push Notifications', 
          value: '', 
          onPress: () => toggleiOSFeature('notifications'),
          toggle: true,
          toggleValue: iOSFeatures.notifications,
        },
        { 
          label: 'Home Screen Widget', 
          value: '', 
          onPress: () => toggleiOSFeature('widgets'),
          toggle: true,
          toggleValue: iOSFeatures.widgets,
        },
        { 
          label: 'Siri Shortcuts', 
          value: '', 
          onPress: () => toggleiOSFeature('siriShortcuts'),
          toggle: true,
          toggleValue: iOSFeatures.siriShortcuts,
        },
        { 
          label: 'Haptic Feedback', 
          value: '', 
          onPress: () => toggleiOSFeature('hapticFeedback'),
          toggle: true,
          toggleValue: iOSFeatures.hapticFeedback,
        },
        { 
          label: 'Offline Mode', 
          value: '', 
          onPress: () => toggleiOSFeature('offlineMode'),
          toggle: true,
          toggleValue: iOSFeatures.offlineMode,
        },
      ],
    }] : []),
    {
      title: 'Data Management',
      items: [
        { label: 'Export Flashcards', value: '', onPress: handleExportData },
        { label: 'Sync Status', value: 'Up to date', onPress: () => {} },
        { label: 'Storage Used', value: '45 MB', onPress: () => {} },
      ],
    },
    {
      title: 'App Settings',
      items: [
        { label: 'Dark Mode', value: 'Off', onPress: () => {} },
        { label: 'Clear Cache', value: '', onPress: handleClearCache },
      ],
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>U</Text>
          </View>
          <Text style={styles.userName}>User</Text>
          <Text style={styles.userEmail}>user@example.com</Text>
        </View>

        {/* Study Stats */}
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{studyStats.cardsStudied}</Text>
            <Text style={styles.statLabel}>Cards Studied</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{studyStats.dayStreak}</Text>
            <Text style={styles.statLabel}>Day Streak</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{studyStats.accuracy}%</Text>
            <Text style={styles.statLabel}>Accuracy</Text>
          </View>
        </View>

        {/* Settings Sections */}
        {settingsOptions.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.settingsSection}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <View style={styles.sectionContent}>
              {section.items.map((item, itemIndex) => (
                <TouchableOpacity
                  key={itemIndex}
                  style={[
                    styles.settingsItem,
                    itemIndex === section.items.length - 1 && styles.lastItem,
                  ]}
                  onPress={item.onPress}
                >
                  <Text style={styles.settingsLabel}>{item.label}</Text>
                  <View style={styles.settingsRight}>
                    {item.toggle ? (
                      <Switch
                        value={item.toggleValue}
                        onValueChange={() => item.onPress()}
                        trackColor={{ false: '#E5E7EB', true: '#3B82F6' }}
                        thumbColor={item.toggleValue ? '#FFFFFF' : '#F3F4F6'}
                      />
                    ) : (
                      <>
                        {item.value && (
                          <Text style={styles.settingsValue}>{item.value}</Text>
                        )}
                        <Text style={styles.chevron}>›</Text>
                      </>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        {/* App Info */}
        <View style={styles.appInfo}>
          <Text style={styles.appVersion}>Document Learning App v1.0.0</Text>
          <Text style={styles.copyright}>© 2024 Your Company</Text>
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
  scrollContent: {
    paddingBottom: 20,
  },
  profileHeader: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: '#FFFFFF',
    marginBottom: 20,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#3B82F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  userName: {
    fontSize: 24,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 16,
    color: '#6B7280',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
  },
  settingsSection: {
    marginHorizontal: 16,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
    marginLeft: 4,
  },
  sectionContent: {
    backgroundColor: '#FFFFFF',
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
  settingsItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  lastItem: {
    borderBottomWidth: 0,
  },
  settingsLabel: {
    fontSize: 16,
    color: '#1F2937',
  },
  settingsRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingsValue: {
    fontSize: 16,
    color: '#6B7280',
    marginRight: 8,
  },
  chevron: {
    fontSize: 18,
    color: '#9CA3AF',
  },
  appInfo: {
    alignItems: 'center',
    padding: 20,
  },
  appVersion: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 4,
  },
  copyright: {
    fontSize: 12,
    color: '#9CA3AF',
  },
});