# Unified Monitoring and Analytics System

This directory contains the unified monitoring and analytics system for the Document Learning App, providing comprehensive tracking, performance monitoring, A/B testing, and user feedback collection across web and iOS platforms.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   iOS App       │    │   Backend API   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Monitoring  │ │    │ │ Monitoring  │ │    │ │ Performance │ │
│ │ Integration │ │    │ │ Service     │ │    │ │ Middleware  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │     Analytics Service       │
                    │                             │
                    │ ┌─────────┐ ┌─────────────┐ │
                    │ │Analytics│ │Performance  │ │
                    │ │Service  │ │Monitor      │ │
                    │ └─────────┘ └─────────────┘ │
                    │ ┌─────────┐ ┌─────────────┐ │
                    │ │A/B Test │ │Feedback     │ │
                    │ │Service  │ │Service      │ │
                    │ └─────────┘ └─────────────┘ │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌───────▼───────┐       ┌───────▼───────┐
    │PostgreSQL │         │     Redis     │       │  Monitoring   │
    │ Database  │         │   Cache       │       │  Dashboard    │
    └───────────┘         └───────────────┘       └───────────────┘
```

## Components

### 1. Analytics Service (`/analytics`)
- **Purpose**: Central analytics and monitoring API
- **Technologies**: Node.js, Express, TypeScript
- **Features**:
  - Event tracking and analytics
  - Performance monitoring
  - A/B testing framework
  - User feedback collection
  - Real-time metrics aggregation

### 2. Monitoring Dashboard (`/dashboard`)
- **Purpose**: Unified monitoring dashboard for all platforms
- **Technologies**: React, TypeScript, Recharts, Tailwind CSS
- **Features**:
  - Real-time performance metrics
  - User analytics visualization
  - Alert management
  - A/B test results
  - Feedback analysis

### 3. Platform Integrations (`/integration`)
- **Web Integration**: JavaScript/TypeScript integration for React frontend
- **iOS Integration**: TypeScript integration for React Native app
- **Features**:
  - Automatic error tracking
  - Performance monitoring
  - User interaction tracking
  - A/B test integration

### 4. Deployment Configuration (`/deployment`)
- **Purpose**: Production deployment setup
- **Technologies**: Docker, Nginx, Prometheus, Grafana
- **Features**:
  - Container orchestration
  - Load balancing
  - SSL termination
  - Monitoring infrastructure

## Quick Start

### Development Setup

1. **Start the analytics service**:
   ```bash
   cd analytics
   npm install
   npm run dev
   ```

2. **Start the monitoring dashboard**:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

3. **Start monitoring infrastructure**:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

### Production Deployment

1. **Configure environment**:
   ```bash
   cd deployment
   cp .env.production .env.local
   # Edit .env.local with your configuration
   ```

2. **Deploy services**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh production
   ```

3. **Verify deployment**:
   ```bash
   ./scripts/health-check.sh
   ```

## Platform Integration

### Web Frontend Integration

Add to your main application file:

```javascript
import { webMonitoring } from './monitoring/integration/web-integration';

// Track feature usage
window.trackFeature('document_upload', 'start');

// Track A/B test conversion
window.trackABTestConversion('upload_flow_v2', 'conversion');

// Submit feedback
window.submitFeedback({
  feedbackType: 'bug',
  title: 'Upload issue',
  description: 'File upload fails on large PDFs',
  rating: 2
});
```

### iOS App Integration

Add to your main App component:

```typescript
import { MonitoredNavigationContainer, useMonitoring } from './monitoring/integration/ios-integration';

export default function App() {
  const monitoring = useMonitoring();
  
  // Track feature usage
  monitoring.trackFeature('flashcard_study', 'start');
  
  // Track A/B test conversion
  monitoring.trackABTestConversion('card_design_v2', 'conversion');
  
  return (
    <MonitoredNavigationContainer>
      {/* Your app content */}
    </MonitoredNavigationContainer>
  );
}
```

## API Endpoints

### Analytics API
- `POST /api/analytics/events` - Track events
- `POST /api/analytics/sessions/start` - Start user session
- `GET /api/analytics/data` - Get analytics data

### Performance API
- `POST /api/performance/metrics` - Record performance metrics
- `GET /api/performance/report` - Get performance report
- `GET /api/performance/alerts` - Get active alerts

### A/B Testing API
- `POST /api/ab-testing/tests` - Create A/B test
- `GET /api/ab-testing/assignment/:testName` - Get test assignment
- `POST /api/ab-testing/events` - Track A/B test events

### Feedback API
- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/analysis` - Get feedback analysis

## Monitoring Dashboards

### Main Dashboard
- **URL**: https://analytics.documentlearning.app/dashboard
- **Features**: Unified view of all platform metrics

### Grafana
- **URL**: https://grafana.documentlearning.app
- **Features**: Advanced metrics visualization and alerting

### Jaeger
- **URL**: https://jaeger.documentlearning.app
- **Features**: Distributed tracing and performance analysis

## Key Metrics Tracked

### Performance Metrics
- **Web**: Page load time, API response time, memory usage, error rate
- **iOS**: App launch time, screen transition time, memory usage, crash rate
- **Backend**: Response time, throughput, error rate, database performance

### User Analytics
- Daily/monthly active users
- Session duration and engagement
- Feature usage patterns
- User journey analysis

### Business Metrics
- Document processing success rate
- Study session completion rate
- User retention and churn
- Feature adoption rates

## Alerting

### Alert Types
- **Critical**: Service down, high error rate, security issues
- **Warning**: Performance degradation, high resource usage
- **Info**: Deployment notifications, scheduled maintenance

### Alert Channels
- Email notifications
- Slack integration
- Dashboard notifications
- PagerDuty integration (configurable)

## A/B Testing

### Test Types Supported
- Feature flags
- UI/UX variations
- Algorithm comparisons
- Content experiments

### Statistical Analysis
- Conversion rate analysis
- Statistical significance testing
- Confidence intervals
- Sample size calculations

## Data Privacy and Security

### Privacy Features
- Data anonymization
- GDPR compliance
- User consent management
- Data retention policies

### Security Measures
- Encrypted data transmission
- Access control and authentication
- Audit logging
- Regular security updates

## Troubleshooting

### Common Issues

1. **Analytics service not receiving data**:
   - Check network connectivity
   - Verify API endpoints
   - Check authentication tokens

2. **Dashboard not loading**:
   - Verify analytics service is running
   - Check CORS configuration
   - Verify environment variables

3. **Alerts not firing**:
   - Check Prometheus configuration
   - Verify alert rules
   - Check AlertManager setup

### Logs and Debugging

```bash
# View analytics service logs
docker-compose logs analytics

# View dashboard logs
docker-compose logs dashboard

# View Prometheus logs
docker-compose logs prometheus

# View all monitoring logs
docker-compose logs -f
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Follow security best practices
5. Test across all platforms

## Support

For issues and questions:
- Create GitHub issues for bugs
- Use discussions for questions
- Check the troubleshooting guide
- Review the API documentation