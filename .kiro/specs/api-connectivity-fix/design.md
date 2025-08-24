# Design Document

## Overview

This design addresses the CORS (Cross-Origin Resource Sharing) issue in the document learning application where the browser blocks requests from localhost:3001 (frontend) to localhost:8000 (backend) due to missing Access-Control-Allow-Origin headers. The solution implements Route A (Vite proxy - recommended) as the primary approach, with Route B (CORS middleware) as an alternative.

## Architecture

### Current CORS Issue

The browser enforces CORS policy when the frontend (http://localhost:3001) makes requests to the backend (http://localhost:8000). Since these are different origins, the browser requires the backend to include Access-Control-Allow-Origin headers, which are currently missing.

### Route A: Vite Proxy Solution (Recommended)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Vite Dev      │    │   Backend API   │
│   localhost:3001│───▶│   Server Proxy  │───▶│   localhost:8000│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    GET /api/documents      Proxy to backend        GET /api/documents
    (Same origin)           (Server-to-server)      (No CORS needed)
         │                       │                       │
         ▼                       ▼                       ▼
    No CORS check          changeOrigin: true       Normal response
```

### Route B: CORS Middleware Solution (Alternative)

```
┌─────────────────┐                            ┌─────────────────┐
│   Browser       │                            │   Backend API   │
│   localhost:3001│───────────────────────────▶│   localhost:8000│
└─────────────────┘                            └─────────────────┘
         │                                               │
    GET http://localhost:8000/api/documents             │
         │                                               │
         ▼                                               ▼
    CORS preflight                              CORSMiddleware
    OPTIONS request                             Access-Control-Allow-Origin
         │                                               │
         ▼                                               ▼
    Allowed by browser                          Normal response
```

## Components and Interfaces

### 1. Vite Proxy Configuration (Route A)

**Purpose**: Configure Vite dev server to proxy API requests to backend

**Configuration**:
```typescript
// vite.config.ts
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const apiTarget = env.VITE_API_BASE_URL || 'http://localhost:8000'
  
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 3001,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})
```

### 2. API Client Configuration (Route A)

**Purpose**: Use relative paths in development, absolute URLs in production

**Interface**:
```typescript
// api.ts
const BASE_URL = import.meta.env.DEV 
  ? '/api'  // Relative path for proxy
  : (import.meta.env.VITE_API_BASE_URL || '/api');

class ApiClient {
  private baseUrl: string = BASE_URL;
  
  async get<T>(endpoint: string): Promise<T> {
    return fetch(`${this.baseUrl}${endpoint}`);
  }
  
  async post<T>(endpoint: string, data: any): Promise<T> {
    return fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: data
    });
  }
}
```

### 3. CORS Middleware Configuration (Route B)

**Purpose**: Configure FastAPI backend to allow cross-origin requests

**Configuration**:
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Environment Configuration

**Purpose**: Support both development and production configurations

**Files**:
```bash
# frontend/.env.development.local
VITE_API_BASE_URL=http://localhost:8000

# frontend/.env.production
VITE_API_BASE_URL=https://api.production.com
```

## Data Models

### Vite Environment Configuration

```typescript
interface ViteEnvConfig {
  VITE_API_BASE_URL?: string;  // Backend URL for production
  DEV: boolean;                // Vite development mode flag
  MODE: 'development' | 'production' | 'test';
}
```

### CORS Configuration Schema

```python
# Backend CORS settings
class CORSConfig:
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001"
    ]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]
```

### API Request Configuration

```typescript
interface ApiRequestConfig {
  baseUrl: string;           // '/api' for dev, full URL for prod
  timeout: number;           // Request timeout in ms
  headers: Record<string, string>;
}
```

## Error Handling

### 1. CORS Error Detection

- Identify CORS errors vs other network failures
- Provide specific error messages for CORS issues
- Guide users to check browser console for CORS errors

### 2. Proxy Configuration Validation

- Verify Vite proxy is correctly configured
- Check that API requests use relative paths in development
- Validate environment variables are properly set

### 3. Backend CORS Validation

- Verify CORS middleware is properly configured
- Check that allowed origins include the frontend URL
- Validate OPTIONS preflight responses return 204 status

```typescript
enum CORSErrorType {
  MISSING_CORS_HEADERS = 'MISSING_CORS_HEADERS',
  INVALID_ORIGIN = 'INVALID_ORIGIN', 
  PREFLIGHT_FAILED = 'PREFLIGHT_FAILED',
  PROXY_MISCONFIGURED = 'PROXY_MISCONFIGURED'
}

class CORSErrorHandler {
  detectCORSError(error: Error): boolean;
  getCORSErrorType(error: Error): CORSErrorType;
  getFixSuggestion(errorType: CORSErrorType): string;
}
```

## Testing Strategy

### 1. CORS Configuration Testing

- **Proxy Testing**: Verify Vite proxy correctly forwards requests
- **Environment Testing**: Test development vs production API configurations
- **Browser Testing**: Verify no CORS errors appear in browser console

### 2. Route A (Proxy) Testing

- Test that API requests use relative paths (/api/*)
- Verify requests appear as localhost:3001/api/* in browser network tab
- Test proxy configuration with different backend URLs

### 3. Route B (CORS) Testing

- Test OPTIONS preflight requests return 204 status
- Verify Access-Control-Allow-Origin headers are present
- Test CORS with different frontend origins

### 4. Integration Testing

- Test file upload functionality works without CORS errors
- Verify API responses are properly received by frontend
- Test error handling when backend is unavailable

## Implementation Approach

### Route A Implementation (Recommended)

1. **Update Vite Configuration**
   - Configure proxy to target localhost:8000
   - Ensure proxy doesn't rewrite /api prefix
   - Set changeOrigin: true and secure: false

2. **Update API Client**
   - Use relative paths (/api/*) in development
   - Use environment variable for production URLs
   - Maintain backward compatibility

3. **Environment Configuration**
   - Create .env.development.local if needed
   - Set VITE_API_BASE_URL for production builds

### Route B Implementation (Alternative)

1. **Backend CORS Configuration**
   - Add CORSMiddleware to FastAPI app
   - Include localhost:3001 in allowed origins
   - Configure proper CORS headers

2. **Verify Backend Entry Point**
   - Ensure uvicorn runs app.main:app
   - Confirm CORS middleware is applied globally
   - Test OPTIONS preflight responses