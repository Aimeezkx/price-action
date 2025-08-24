# CORS Solution Documentation

## Overview

This document describes the CORS (Cross-Origin Resource Sharing) solution implemented for the Document Learning Application to resolve API connectivity issues between the frontend (localhost:3001) and backend (localhost:8000).

## Problem Statement

The application was experiencing CORS errors when the frontend attempted to make API requests to the backend. The browser was blocking requests due to missing `Access-Control-Allow-Origin` headers, resulting in `SERVICE_UNAVAILABLE/NETWORK_UNREACHABLE` errors.

## Implemented Solution

**Hybrid Approach: Route A (Vite Proxy) + Route B (CORS Middleware)**

Both solutions were implemented to provide maximum compatibility and flexibility:

### Route A: Vite Proxy Solution (Primary - Development)

**Configuration:**
- **File:** `frontend/vite.config.ts`
- **Proxy Target:** `http://localhost:8000` (configurable via `VITE_API_BASE_URL`)
- **Proxy Path:** `/api/*` requests are proxied to the backend
- **Settings:** `changeOrigin: true`, `secure: false`

**API Client Configuration:**
- **File:** `frontend/src/lib/api.ts`
- **Development:** Uses relative paths (`/api`) for proxy compatibility
- **Production:** Uses `VITE_API_BASE_URL` environment variable

### Route B: CORS Middleware Solution (Fallback - Production)

**Configuration:**
- **File:** `backend/main.py`
- **Middleware:** FastAPI `CORSMiddleware`
- **Allowed Origins:**
  - `http://localhost:3000`
  - `http://localhost:3001`
  - `http://127.0.0.1:3000`
  - `http://127.0.0.1:3001`
  - `http://frontend:3000` (Docker)
- **Settings:** `allow_credentials=True`, all methods and headers allowed

## Setup Instructions for Developers

### Prerequisites
- Node.js and npm installed
- Python 3.8+ with FastAPI dependencies
- Both frontend and backend repositories cloned

### Development Setup

1. **Backend Setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Environment Configuration:**
   - The frontend will automatically use the Vite proxy in development
   - No additional configuration needed for basic setup
   - Optional: Create `frontend/.env.development.local` to override proxy target:
     ```
     VITE_API_BASE_URL=http://localhost:8000
     ```

### Production Setup

1. **Environment Variables:**
   ```bash
   # frontend/.env.production
   VITE_API_BASE_URL=https://your-api-domain.com
   ```

2. **Build and Deploy:**
   ```bash
   cd frontend
   npm run build
   # Deploy dist/ folder to your web server
   ```

## Verification Steps

### 1. Verify Proxy is Working (Development)

1. Start both backend and frontend servers
2. Open browser developer tools (F12)
3. Navigate to the application at `http://localhost:3001`
4. Check the Network tab:
   - API requests should show as `localhost:3001/api/*` (not `localhost:8000`)
   - No CORS errors should appear in the Console tab

### 2. Verify CORS Headers (Production/Direct Requests)

1. Test OPTIONS preflight request:
   ```bash
   curl -X OPTIONS http://localhost:8000/api/health \
     -H "Origin: http://localhost:3001" \
     -H "Access-Control-Request-Method: GET" \
     -v
   ```

2. Expected response:
   - Status: `204 No Content`
   - Headers should include:
     - `Access-Control-Allow-Origin: http://localhost:3001`
     - `Access-Control-Allow-Methods: *`
     - `Access-Control-Allow-Headers: *`

### 3. Test File Upload Functionality

1. Navigate to the document upload page
2. Select and upload a test file
3. Verify:
   - No CORS errors in browser console
   - Upload completes successfully
   - Backend returns proper JSON response (not 500 error)

## Troubleshooting Guide

### Common CORS Issues

#### Issue: "CORS policy: No 'Access-Control-Allow-Origin' header"
**Symptoms:** Direct API requests fail with CORS error
**Solution:**
1. Verify backend CORS middleware is configured correctly
2. Check that frontend origin is in allowed origins list
3. Ensure CORS middleware is added before other middleware

#### Issue: "Failed to fetch" or "Network Error"
**Symptoms:** API requests fail without specific CORS error
**Solutions:**
1. Check if backend server is running on correct port (8000)
2. Verify Vite proxy configuration in `vite.config.ts`
3. Check browser network tab for actual request URLs

#### Issue: Proxy not working in development
**Symptoms:** Requests still go to `localhost:8000` instead of being proxied
**Solutions:**
1. Restart Vite dev server after config changes
2. Verify API client uses relative paths (`/api`) in development
3. Check `import.meta.env.DEV` is true in development

#### Issue: Production build can't reach API
**Symptoms:** Works in development but fails in production
**Solutions:**
1. Set correct `VITE_API_BASE_URL` in production environment
2. Ensure production API server has CORS configured
3. Check network requests use absolute URLs in production

### Debug Commands

```bash
# Test backend health endpoint
curl http://localhost:8000/api/health

# Test CORS preflight
curl -X OPTIONS http://localhost:8000/api/documents \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Check Vite proxy in development
# (Network tab should show localhost:3001/api/* requests)
```

### Environment Variables Reference

| Variable | Environment | Purpose | Example |
|----------|-------------|---------|---------|
| `VITE_API_BASE_URL` | Development | Override proxy target | `http://localhost:8000` |
| `VITE_API_BASE_URL` | Production | API server URL | `https://api.example.com` |

## Architecture Decision

**Why Hybrid Approach?**

1. **Development Efficiency:** Vite proxy eliminates CORS issues during development
2. **Production Flexibility:** CORS middleware supports various deployment scenarios
3. **Team Compatibility:** Different team members can use either approach
4. **Deployment Options:** Supports both same-origin and cross-origin deployments

**Recommended Usage:**
- **Development:** Use Vite proxy (Route A) - automatic with `npm run dev`
- **Production:** Configure based on deployment architecture
  - Same domain: Use built frontend with relative paths
  - Different domains: Use CORS middleware (Route B)

## Security Considerations

1. **CORS Origins:** Only include necessary origins in production
2. **Credentials:** `allow_credentials=True` should be used carefully
3. **Headers:** Consider restricting allowed headers in production
4. **Environment Variables:** Keep production API URLs secure

## Maintenance Notes

- Update allowed origins when adding new frontend domains
- Monitor CORS errors in production logs
- Test CORS configuration when updating FastAPI or Vite versions
- Document any custom CORS requirements for specific endpoints