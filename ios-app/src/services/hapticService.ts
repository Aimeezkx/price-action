import ReactNativeHapticFeedback from 'react-native-haptic-feedback';
import { Platform } from 'react-native';

export type HapticFeedbackType = 
  | 'selection'
  | 'impactLight'
  | 'impactMedium'
  | 'impactHeavy'
  | 'notificationSuccess'
  | 'notificationWarning'
  | 'notificationError';

export interface HapticOptions {
  enableVibrateFallback?: boolean;
  ignoreAndroidSystemSettings?: boolean;
}

class HapticService {
  private isEnabled: boolean = true;
  private defaultOptions: HapticOptions = {
    enableVibrateFallback: true,
    ignoreAndroidSystemSettings: false,
  };

  constructor() {
    this.initializeHaptics();
  }

  private async initializeHaptics(): Promise<void> {
    // Check if haptic feedback is supported
    if (Platform.OS === 'ios') {
      // iOS always supports haptic feedback on supported devices
      this.isEnabled = true;
    } else {
      // Android support varies by device
      this.isEnabled = true; // Assume supported, will fallback to vibration if needed
    }
  }

  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  isHapticEnabled(): boolean {
    return this.isEnabled;
  }

  // Card interaction haptics
  async cardFlip(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactLight', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async cardGrade(grade: number): Promise<void> {
    if (!this.isEnabled) return;

    try {
      if (grade >= 4) {
        // Good grade - success haptic
        ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      } else if (grade >= 2) {
        // Medium grade - light impact
        ReactNativeHapticFeedback.trigger('impactMedium', this.defaultOptions);
      } else {
        // Poor grade - warning haptic
        ReactNativeHapticFeedback.trigger('notificationWarning', this.defaultOptions);
      }
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async cardSwipe(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('selection', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Navigation haptics
  async buttonPress(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactLight', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async tabSwitch(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('selection', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async menuOpen(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactMedium', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Study session haptics
  async sessionStart(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async sessionComplete(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      // Double success haptic for session completion
      ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      setTimeout(() => {
        ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      }, 100);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async streakAchievement(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      // Triple success haptic for achievements
      ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      setTimeout(() => {
        ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      }, 100);
      setTimeout(() => {
        ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      }, 200);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Error and warning haptics
  async error(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('notificationError', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async warning(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('notificationWarning', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Image hotspot haptics
  async hotspotHit(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactMedium', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async hotspotMiss(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactLight', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Document interaction haptics
  async documentUpload(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactMedium', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async documentProcessingComplete(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async documentProcessingError(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('notificationError', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Search haptics
  async searchResult(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('selection', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  async searchNoResults(): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      ReactNativeHapticFeedback.trigger('impactLight', this.defaultOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Generic haptic methods
  async trigger(type: HapticFeedbackType, options?: HapticOptions): Promise<void> {
    if (!this.isEnabled) return;
    
    try {
      const hapticOptions = { ...this.defaultOptions, ...options };
      ReactNativeHapticFeedback.trigger(type, hapticOptions);
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  // Haptic patterns for complex interactions
  async playPattern(pattern: { type: HapticFeedbackType; delay: number }[]): Promise<void> {
    if (!this.isEnabled) return;

    try {
      for (let i = 0; i < pattern.length; i++) {
        const { type, delay } = pattern[i];
        
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, delay));
        }
        
        ReactNativeHapticFeedback.trigger(type, this.defaultOptions);
      }
    } catch (error) {
      console.warn('Haptic pattern failed:', error);
    }
  }

  // Contextual haptic feedback based on user performance
  async performanceBasedHaptic(accuracy: number, speed: number): Promise<void> {
    if (!this.isEnabled) return;

    try {
      if (accuracy >= 0.9 && speed >= 0.8) {
        // Excellent performance
        await this.playPattern([
          { type: 'notificationSuccess', delay: 0 },
          { type: 'impactLight', delay: 100 },
        ]);
      } else if (accuracy >= 0.7) {
        // Good performance
        ReactNativeHapticFeedback.trigger('notificationSuccess', this.defaultOptions);
      } else if (accuracy >= 0.5) {
        // Average performance
        ReactNativeHapticFeedback.trigger('impactMedium', this.defaultOptions);
      } else {
        // Poor performance
        ReactNativeHapticFeedback.trigger('notificationWarning', this.defaultOptions);
      }
    } catch (error) {
      console.warn('Performance haptic failed:', error);
    }
  }

  // Adaptive haptic intensity based on user preferences
  async adaptiveHaptic(baseType: HapticFeedbackType, intensity: 'light' | 'medium' | 'heavy'): Promise<void> {
    if (!this.isEnabled) return;

    try {
      let hapticType: HapticFeedbackType;
      
      switch (intensity) {
        case 'light':
          hapticType = baseType === 'impactMedium' || baseType === 'impactHeavy' 
            ? 'impactLight' 
            : baseType;
          break;
        case 'heavy':
          hapticType = baseType === 'impactLight' || baseType === 'impactMedium' 
            ? 'impactHeavy' 
            : baseType;
          break;
        default:
          hapticType = baseType;
      }
      
      ReactNativeHapticFeedback.trigger(hapticType, this.defaultOptions);
    } catch (error) {
      console.warn('Adaptive haptic failed:', error);
    }
  }
}

export const hapticService = new HapticService();