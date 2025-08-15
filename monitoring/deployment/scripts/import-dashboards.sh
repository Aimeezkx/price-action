#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-"admin123"}

echo -e "${YELLOW}Importing Grafana dashboards...${NC}"

# Wait for Grafana to be ready
echo -n "Waiting for Grafana to be ready... "
for i in {1..30}; do
    if curl -s -f "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Grafana not ready after 30 attempts${NC}"
        exit 1
    fi
    sleep 2
done

# Function to import dashboard
import_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    echo -n "Importing $dashboard_name... "
    
    if response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        -d @"$dashboard_file" \
        "$GRAFANA_URL/api/dashboards/db"); then
        
        if echo "$response" | grep -q '"status":"success"'; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗ $(echo "$response" | jq -r '.message // "Unknown error"')${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to connect${NC}"
    fi
}

# Create dashboards directory if it doesn't exist
mkdir -p ../grafana/dashboards

# Create platform overview dashboard
cat > ../grafana/dashboards/platform-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Document Learning App - Platform Overview",
    "tags": ["document-learning", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Active Users by Platform",
        "type": "stat",
        "targets": [
          {
            "expr": "sum by (platform) (rate(user_sessions_total[5m]))",
            "legendFormat": "{{platform}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time by Platform",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{platform}} - 95th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate by Platform",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "{{platform}} error rate"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Memory Usage by Platform",
        "type": "timeseries",
        "targets": [
          {
            "expr": "process_resident_memory_bytes",
            "legendFormat": "{{platform}} memory"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 5,
        "title": "Active Alerts",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "format": "table"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  },
  "overwrite": true
}
EOF

# Create user analytics dashboard
cat > ../grafana/dashboards/user-analytics.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Document Learning App - User Analytics",
    "tags": ["document-learning", "analytics"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Daily Active Users",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum by (platform) (daily_active_users)",
            "legendFormat": "{{platform}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Session Duration",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(session_duration_seconds_bucket[5m]))",
            "legendFormat": "Median"
          },
          {
            "expr": "histogram_quantile(0.95, rate(session_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Feature Usage",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (feature) (rate(feature_usage_total[1h]))",
            "legendFormat": "{{feature}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "User Feedback Sentiment",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (sentiment) (feedback_sentiment_total)",
            "legendFormat": "{{sentiment}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-24h", "to": "now"},
    "refresh": "5m"
  },
  "overwrite": true
}
EOF

# Import all dashboards
for dashboard in ../grafana/dashboards/*.json; do
    if [ -f "$dashboard" ]; then
        import_dashboard "$dashboard"
    fi
done

echo -e "${GREEN}Dashboard import completed!${NC}"