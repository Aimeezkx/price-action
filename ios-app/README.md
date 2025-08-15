# Document Learning iOS App

A React Native iOS application for the Document Learning platform, providing flashcard-based learning with spaced repetition.

## Features

### 📚 Study Interface
- **Flashcard Learning**: Interactive cards with flip animations
- **Spaced Repetition**: 0-5 grading system for optimal learning
- **Progress Tracking**: Real-time session statistics and accuracy
- **Multiple Card Types**: Q&A, Cloze deletion, and Image hotspot cards

### 📄 Document Management
- **Document Upload**: Support for PDF and DOCX files
- **Processing Status**: Real-time status updates
- **Document Library**: Browse and manage uploaded documents

### 🔍 Search & Discovery
- **Knowledge Search**: Find relevant information across documents
- **Card Search**: Locate specific flashcards
- **Contextual Results**: See source chapters and highlights

### 👤 Profile & Settings
- **Study Statistics**: Track progress and streaks
- **Export Options**: Anki and Notion format support
- **App Settings**: Customization and preferences

## Architecture

### Shared Backend
- Uses the same FastAPI backend as the web application
- RESTful API with consistent endpoints
- Real-time synchronization between platforms

### React Native Structure
```
ios-app/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── FlashCard.tsx    # Card display with animations
│   │   └── GradingInterface.tsx # 0-5 grading buttons
│   ├── screens/             # Main app screens
│   │   ├── StudyScreen.tsx  # Flashcard study interface
│   │   ├── DocumentsScreen.tsx # Document management
│   │   ├── SearchScreen.tsx # Search functionality
│   │   └── ProfileScreen.tsx # User profile & settings
│   ├── navigation/          # App navigation
│   ├── services/            # API client
│   ├── hooks/              # React Query hooks
│   └── types/              # TypeScript definitions
├── App.tsx                 # Root component
└── package.json           # Dependencies
```

## Installation

### Prerequisites
- Node.js 16+
- React Native CLI
- Xcode (for iOS development)
- iOS Simulator or physical device

### Setup
```bash
# Navigate to iOS app directory
cd ios-app

# Install dependencies
npm install

# Install iOS dependencies
cd ios && pod install && cd ..

# Start Metro bundler
npm start

# Run on iOS simulator
npm run ios
```

## Development

### API Configuration
Update the API base URL in `src/services/api.ts`:
```typescript
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000/api'  // Development
  : 'https://your-api-domain.com/api';  // Production
```

### Key Components

#### FlashCard Component
- 3D flip animations using React Native Animated API
- Support for all card types (Q&A, cloze, image hotspot)
- Touch-friendly interface with haptic feedback

#### GradingInterface Component
- 0-5 scale grading with color-coded buttons
- Touch-optimized layout for mobile devices
- Immediate feedback and progression

#### StudyScreen
- Complete study session management
- Progress tracking and statistics
- Navigation controls and keyboard shortcuts

## Features Comparison

| Feature | Web App | iOS App |
|---------|---------|---------|
| Flashcard Study | ✅ | ✅ |
| Card Flip Animation | CSS 3D | React Native Animated |
| Keyboard Shortcuts | ✅ | Touch Optimized |
| Document Upload | ✅ | ✅ (Native Picker) |
| Search | ✅ | ✅ |
| Export | ✅ | ✅ |
| Offline Support | ❌ | 🔄 (Planned) |
| Push Notifications | ❌ | 🔄 (Planned) |

## API Integration

The iOS app uses the same backend API as the web application:

### Endpoints Used
- `GET /api/review/today` - Today's review cards
- `POST /api/review/grade` - Grade a card
- `GET /api/cards` - Get cards with filters
- `GET /api/documents` - List documents
- `POST /api/ingest` - Upload document
- `GET /api/search` - Search knowledge and cards

### Authentication
- Token-based authentication using AsyncStorage
- Automatic token refresh
- Secure API communication

## Deployment

### iOS App Store
1. Configure app signing in Xcode
2. Update bundle identifier and version
3. Build release version
4. Submit to App Store Connect

### TestFlight Distribution
1. Archive the app in Xcode
2. Upload to App Store Connect
3. Add internal/external testers
4. Distribute beta builds

## Future Enhancements

### Planned Features
- **Offline Support**: Study without internet connection
- **Push Notifications**: Daily study reminders
- **Apple Watch**: Quick review sessions
- **Siri Shortcuts**: Voice-activated study sessions
- **Widget Support**: Study progress on home screen
- **Dark Mode**: System-wide dark theme support

### Performance Optimizations
- Image caching for faster card loading
- Background sync for seamless experience
- Memory optimization for large document sets
- Battery usage optimization

## Contributing

1. Follow React Native best practices
2. Use TypeScript for type safety
3. Test on both simulator and physical devices
4. Maintain consistency with web app UX
5. Follow iOS Human Interface Guidelines

## License

Same license as the main Document Learning application.