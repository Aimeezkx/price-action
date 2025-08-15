import { AccessibilityInfo, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface AccessibilityConfig {
  enableVoiceOver: boolean;
  enableHighContrast: boolean;
  enableLargeText: boolean;
  enableReducedMotion: boolean;
  customFontSize: number;
  customColors: {
    primary: string;
    secondary: string;
    background: string;
    text: string;
  };
}

export interface AccessibilityState {
  isScreenReaderEnabled: boolean;
  isReduceMotionEnabled: boolean;
  isReduceTransparencyEnabled: boolean;
  isBoldTextEnabled: boolean;
  isGrayscaleEnabled: boolean;
  isInvertColorsEnabled: boolean;
  prefersCrossFadeTransitions: boolean;
}

export interface AccessibilityLabels {
  [key: string]: {
    label: string;
    hint?: string;
    role?: string;
    state?: any;
  };
}

class AccessibilityService {
  private readonly DEFAULT_CONFIG: AccessibilityConfig = {
    enableVoiceOver: true,
    enableHighContrast: false,
    enableLargeText: false,
    enableReducedMotion: false,
    customFontSize: 16,
    customColors: {
      primary: '#007AFF',
      secondary: '#5856D6',
      background: '#FFFFFF',
      text: '#000000',
    },
  };

  private readonly ACCESSIBILITY_CONFIG_KEY = 'accessibility_config';
  private readonly ACCESSIBILITY_LABELS_KEY = 'accessibility_labels';

  private config: AccessibilityConfig;
  private accessibilityState: AccessibilityState = {
    isScreenReaderEnabled: false,
    isReduceMotionEnabled: false,
    isReduceTransparencyEnabled: false,
    isBoldTextEnabled: false,
    isGrayscaleEnabled: false,
    isInvertColorsEnabled: false,
    prefersCrossFadeTransitions: false,
  };
  
  private listeners: ((state: AccessibilityState) => void)[] = [];
  private accessibilityLabels: AccessibilityLabels = {};

  constructor(config?: Partial<AccessibilityConfig>) {
    this.config = { ...this.DEFAULT_CONFIG, ...config };
  }

  async initializeAccessibility(): Promise<void> {
    console.log('Initializing accessibility service');
    
    try {
      // Load saved configuration
      await this.loadConfig();
      await this.loadAccessibilityLabels();
      
      // Check current accessibility state
      await this.updateAccessibilityState();
      
      // Set up accessibility event listeners
      this.setupAccessibilityListeners();
      
      console.log('Accessibility service initialized');
    } catch (error) {
      console.error('Failed to initialize accessibility service:', error);
    }
  }

  private setupAccessibilityListeners(): void {
    // Listen for screen reader changes
    AccessibilityInfo.addEventListener('screenReaderChanged', (isEnabled: boolean) => {
      this.accessibilityState.isScreenReaderEnabled = isEnabled;
      this.notifyListeners();
      
      if (isEnabled) {
        console.log('Screen reader enabled');
        this.optimizeForScreenReader();
      } else {
        console.log('Screen reader disabled');
      }
    });

    // Listen for reduce motion changes
    AccessibilityInfo.addEventListener('reduceMotionChanged', (isEnabled: boolean) => {
      this.accessibilityState.isReduceMotionEnabled = isEnabled;
      this.notifyListeners();
      
      if (isEnabled) {
        console.log('Reduce motion enabled');
        this.optimizeForReducedMotion();
      }
    });

    // Listen for bold text changes (iOS only)
    if (Platform.OS === 'ios') {
      AccessibilityInfo.addEventListener('boldTextChanged', (isEnabled: boolean) => {
        this.accessibilityState.isBoldTextEnabled = isEnabled;
        this.notifyListeners();
        
        if (isEnabled) {
          console.log('Bold text enabled');
          this.optimizeForBoldText();
        }
      });

      AccessibilityInfo.addEventListener('grayscaleChanged', (isEnabled: boolean) => {
        this.accessibilityState.isGrayscaleEnabled = isEnabled;
        this.notifyListeners();
      });

      AccessibilityInfo.addEventListener('invertColorsChanged', (isEnabled: boolean) => {
        this.accessibilityState.isInvertColorsEnabled = isEnabled;
        this.notifyListeners();
        
        if (isEnabled) {
          this.optimizeForInvertedColors();
        }
      });

      AccessibilityInfo.addEventListener('reduceTransparencyChanged', (isEnabled: boolean) => {
        this.accessibilityState.isReduceTransparencyEnabled = isEnabled;
        this.notifyListeners();
        
        if (isEnabled) {
          this.optimizeForReducedTransparency();
        }
      });
    }
  }

  private async updateAccessibilityState(): Promise<void> {
    try {
      const [
        isScreenReaderEnabled,
        isReduceMotionEnabled,
        isReduceTransparencyEnabled,
        isBoldTextEnabled,
        isGrayscaleEnabled,
        isInvertColorsEnabled,
      ] = await Promise.all([
        AccessibilityInfo.isScreenReaderEnabled(),
        AccessibilityInfo.isReduceMotionEnabled(),
        Platform.OS === 'ios' ? AccessibilityInfo.isReduceTransparencyEnabled() : Promise.resolve(false),
        Platform.OS === 'ios' ? AccessibilityInfo.isBoldTextEnabled() : Promise.resolve(false),
        Platform.OS === 'ios' ? AccessibilityInfo.isGrayscaleEnabled() : Promise.resolve(false),
        Platform.OS === 'ios' ? AccessibilityInfo.isInvertColorsEnabled() : Promise.resolve(false),
      ]);

      this.accessibilityState = {
        isScreenReaderEnabled,
        isReduceMotionEnabled,
        isReduceTransparencyEnabled,
        isBoldTextEnabled,
        isGrayscaleEnabled,
        isInvertColorsEnabled,
        prefersCrossFadeTransitions: isReduceMotionEnabled,
      };

      this.notifyListeners();
    } catch (error) {
      console.error('Failed to update accessibility state:', error);
    }
  }

  private optimizeForScreenReader(): void {
    // Optimize app for screen reader usage
    console.log('Optimizing for screen reader');
    
    // Ensure all interactive elements have proper accessibility labels
    this.validateAccessibilityLabels();
    
    // Disable auto-playing content
    // Increase touch target sizes
    // Simplify navigation
  }

  private optimizeForReducedMotion(): void {
    // Disable or reduce animations
    console.log('Optimizing for reduced motion');
    
    // This would integrate with animation libraries to disable/reduce animations
    // For example, disable card flip animations, reduce transition durations
  }

  private optimizeForBoldText(): void {
    // Adjust font weights and sizes
    console.log('Optimizing for bold text');
    
    // Increase font weights
    // Adjust spacing for better readability
  }

  private optimizeForInvertedColors(): void {
    // Adjust colors for inverted color schemes
    console.log('Optimizing for inverted colors');
    
    // Ensure proper contrast ratios
    // Adjust image rendering
  }

  private optimizeForReducedTransparency(): void {
    // Remove or reduce transparency effects
    console.log('Optimizing for reduced transparency');
    
    // Make backgrounds more opaque
    // Increase contrast
  }

  private validateAccessibilityLabels(): void {
    // Check if all required accessibility labels are present
    const requiredLabels = [
      'flashcard_front',
      'flashcard_back',
      'grade_button',
      'next_card_button',
      'previous_card_button',
      'document_upload_button',
      'search_input',
      'chapter_navigation',
      'image_hotspot',
    ];

    const missingLabels = requiredLabels.filter(key => !this.accessibilityLabels[key]);
    
    if (missingLabels.length > 0) {
      console.warn('Missing accessibility labels:', missingLabels);
    }
  }

  // Accessibility label management
  setAccessibilityLabel(key: string, label: string, hint?: string, role?: string, state?: any): void {
    this.accessibilityLabels[key] = {
      label,
      hint,
      role,
      state,
    };
    
    this.saveAccessibilityLabels();
  }

  getAccessibilityLabel(key: string): AccessibilityLabels[string] | null {
    return this.accessibilityLabels[key] || null;
  }

  // Generate accessibility props for components
  getAccessibilityProps(key: string, overrides?: Partial<AccessibilityLabels[string]>) {
    const labelData = this.accessibilityLabels[key];
    if (!labelData) {
      console.warn(`No accessibility label found for key: ${key}`);
      return {};
    }

    const props: any = {
      accessible: true,
      accessibilityLabel: labelData.label,
    };

    if (labelData.hint || overrides?.hint) {
      props.accessibilityHint = overrides?.hint || labelData.hint;
    }

    if (labelData.role || overrides?.role) {
      props.accessibilityRole = overrides?.role || labelData.role;
    }

    if (labelData.state || overrides?.state) {
      props.accessibilityState = { ...labelData.state, ...overrides?.state };
    }

    return props;
  }

  // Announce messages to screen reader
  announceForAccessibility(message: string): void {
    if (this.accessibilityState.isScreenReaderEnabled) {
      AccessibilityInfo.announceForAccessibility(message);
    }
  }

  // Set focus to specific element (for screen readers)
  setAccessibilityFocus(reactTag: number): void {
    if (this.accessibilityState.isScreenReaderEnabled) {
      AccessibilityInfo.setAccessibilityFocus(reactTag);
    }
  }

  // Get current accessibility state
  getAccessibilityState(): AccessibilityState {
    return { ...this.accessibilityState };
  }

  // Check if specific accessibility feature is enabled
  isAccessibilityFeatureEnabled(feature: keyof AccessibilityState): boolean {
    return this.accessibilityState[feature];
  }

  // Get recommended font size based on accessibility settings
  getRecommendedFontSize(baseFontSize: number): number {
    let fontSize = baseFontSize;
    
    if (this.config.enableLargeText) {
      fontSize *= 1.2;
    }
    
    if (this.accessibilityState.isBoldTextEnabled) {
      fontSize *= 1.1;
    }
    
    if (this.config.customFontSize !== this.DEFAULT_CONFIG.customFontSize) {
      fontSize = this.config.customFontSize;
    }
    
    return Math.round(fontSize);
  }

  // Get recommended colors based on accessibility settings
  getRecommendedColors() {
    let colors = { ...this.config.customColors };
    
    if (this.config.enableHighContrast) {
      colors = {
        primary: '#000000',
        secondary: '#333333',
        background: '#FFFFFF',
        text: '#000000',
      };
    }
    
    if (this.accessibilityState.isInvertColorsEnabled) {
      // Colors will be inverted by the system, so we don't need to change them
    }
    
    return colors;
  }

  // Initialize default accessibility labels
  private initializeDefaultLabels(): void {
    const defaultLabels: AccessibilityLabels = {
      flashcard_front: {
        label: 'Flashcard front side',
        hint: 'Tap to flip to back side',
        role: 'button',
      },
      flashcard_back: {
        label: 'Flashcard back side',
        hint: 'Tap to flip to front side',
        role: 'button',
      },
      grade_button_0: {
        label: 'Grade 0 - Complete blackout',
        hint: 'Tap to grade this card as completely forgotten',
        role: 'button',
      },
      grade_button_1: {
        label: 'Grade 1 - Incorrect response',
        hint: 'Tap to grade this card as incorrect',
        role: 'button',
      },
      grade_button_2: {
        label: 'Grade 2 - Incorrect but remembered',
        hint: 'Tap to grade this card as incorrect but partially remembered',
        role: 'button',
      },
      grade_button_3: {
        label: 'Grade 3 - Correct with difficulty',
        hint: 'Tap to grade this card as correct but difficult',
        role: 'button',
      },
      grade_button_4: {
        label: 'Grade 4 - Correct with hesitation',
        hint: 'Tap to grade this card as correct with some hesitation',
        role: 'button',
      },
      grade_button_5: {
        label: 'Grade 5 - Perfect response',
        hint: 'Tap to grade this card as perfectly remembered',
        role: 'button',
      },
      document_upload_button: {
        label: 'Upload document',
        hint: 'Tap to select and upload a document for processing',
        role: 'button',
      },
      search_input: {
        label: 'Search cards and content',
        hint: 'Enter text to search through your flashcards and documents',
        role: 'searchbox',
      },
      chapter_navigation: {
        label: 'Chapter navigation',
        hint: 'Navigate through document chapters',
        role: 'tablist',
      },
      image_hotspot: {
        label: 'Image hotspot',
        hint: 'Tap to reveal information about this area of the image',
        role: 'button',
      },
      next_card_button: {
        label: 'Next card',
        hint: 'Move to the next flashcard',
        role: 'button',
      },
      previous_card_button: {
        label: 'Previous card',
        hint: 'Move to the previous flashcard',
        role: 'button',
      },
    };

    this.accessibilityLabels = { ...this.accessibilityLabels, ...defaultLabels };
  }

  private async loadConfig(): Promise<void> {
    try {
      const configJson = await AsyncStorage.getItem(this.ACCESSIBILITY_CONFIG_KEY);
      if (configJson) {
        const savedConfig = JSON.parse(configJson);
        this.config = { ...this.config, ...savedConfig };
      }
    } catch (error) {
      console.error('Failed to load accessibility config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      await AsyncStorage.setItem(this.ACCESSIBILITY_CONFIG_KEY, JSON.stringify(this.config));
    } catch (error) {
      console.error('Failed to save accessibility config:', error);
    }
  }

  private async loadAccessibilityLabels(): Promise<void> {
    try {
      const labelsJson = await AsyncStorage.getItem(this.ACCESSIBILITY_LABELS_KEY);
      if (labelsJson) {
        const savedLabels = JSON.parse(labelsJson);
        this.accessibilityLabels = { ...this.accessibilityLabels, ...savedLabels };
      } else {
        this.initializeDefaultLabels();
        await this.saveAccessibilityLabels();
      }
    } catch (error) {
      console.error('Failed to load accessibility labels:', error);
      this.initializeDefaultLabels();
    }
  }

  private async saveAccessibilityLabels(): Promise<void> {
    try {
      await AsyncStorage.setItem(this.ACCESSIBILITY_LABELS_KEY, JSON.stringify(this.accessibilityLabels));
    } catch (error) {
      console.error('Failed to save accessibility labels:', error);
    }
  }

  async updateConfig(newConfig: Partial<AccessibilityConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();
    console.log('Accessibility config updated:', this.config);
  }

  addAccessibilityStateListener(listener: (state: AccessibilityState) => void): () => void {
    this.listeners.push(listener);
    
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.accessibilityState);
      } catch (error) {
        console.error('Accessibility state listener error:', error);
      }
    });
  }
}

export const accessibilityService = new AccessibilityService();