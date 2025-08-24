# Document Learning App - Frontend

React frontend for the Document Learning App.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

### Code Quality

- **Linting**: ESLint with TypeScript support
- **Type Checking**: TypeScript compiler
- **Styling**: Tailwind CSS

### Environment Variables

The application uses Vite's proxy feature for API requests in development. Configure the following environment variables:

#### Development
Create a `.env.local` or `.env.development.local` file with:

```bash
# Backend URL for Vite proxy (defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

In development mode, API requests use relative paths (`/api/*`) and are automatically proxied to the backend.

#### Production
Create a `.env.production` file with:

```bash
# Full API base URL for production
VITE_API_BASE_URL=https://api.yourdomain.com
```

#### CORS Solution
This application uses a **Hybrid CORS Solution** combining Vite Proxy and CORS Middleware:

**Route A - Vite Proxy (Primary for Development):**
- Vite dev server proxies `/api/*` requests to the backend
- API client uses relative paths (`/api`) in development mode
- Eliminates CORS issues by making same-origin requests
- Automatic configuration - no setup required

**Route B - CORS Middleware (Fallback for Production):**
- Backend includes FastAPI CORSMiddleware
- Supports direct cross-origin requests
- Configured for localhost:3001 and production domains

### Verification Steps

1. **Start Development Servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend && uvicorn main:app --reload
   
   # Terminal 2 - Frontend  
   cd frontend && npm run dev
   ```

2. **Verify Proxy is Working:**
   - Open http://localhost:3001 in browser
   - Open Developer Tools (F12) → Network tab
   - API requests should show as `localhost:3001/api/*` (not `localhost:8000`)
   - Console should show no CORS errors

3. **Test File Upload:**
   - Navigate to document upload page
   - Upload a test file
   - Verify successful upload without CORS errors

### Troubleshooting

**Issue: API requests still go to localhost:8000**
- Restart Vite dev server after config changes
- Check that API client uses relative paths in development

**Issue: "Failed to fetch" errors**
- Verify backend is running on port 8000
- Check Vite proxy configuration in `vite.config.ts`

**Issue: Production build can't reach API**
- Set correct `VITE_API_BASE_URL` in production environment
- Ensure production API server has CORS configured

For detailed troubleshooting, see `../CORS_SOLUTION_DOCUMENTATION.md`.