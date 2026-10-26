# Dashboard & API Integration Implementation Guide

## Overview

This implementation adds a fully functional dashboard with authentication, real-time investigation progress tracking, and investigation history management. The system is built with:

- **Frontend**: Next.js with InsForge SDK for authentication and real-time capabilities
- **Backend**: FastAPI with InsForge integration for database operations
- **Database**: InsForge-managed PostgreSQL

## Architecture

```
Frontend (Next.js + React)
├── AuthProvider (InsForge Auth)
├── Dashboard
│   ├── Investigation CTA
│   ├── Real-time Progress Display
│   ├── Root Cause Results Card
│   └── Investigation History Table
└── Login/Sign Up Page

Backend (FastAPI)
├── POST /investigate (with auth token)
├── GET /investigations/history
├── InsForge Database Integration
└── InsForge Real-time Publishing

InsForge Backend
├── Authentication
├── Database (investigations table)
└── Real-time Channels
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.10+
- InsForge CLI: `npm install -g @insforge/cli`
- Active InsForge project linked via `.insforge/project.json`

### Backend Setup

1. **Get InsForge credentials:**
   ```bash
   cd backend
   npx @insforge/cli secrets get ANON_KEY
   npx @insforge/cli secrets get API_KEY
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with InsForge credentials:**
   ```
   INSFORGE_URL=https://your-project.us-east.insforge.app
   INSFORGE_API_KEY=your-api-key
   OPENROUTER_API_KEY=your-openrouter-key
   OPENROUTER_MODEL=openai/gpt-4o-mini
   ```

4. **Get the InsForge URL from:**
   ```bash
   cat .insforge/project.json | grep oss_host
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Run backend:**
   ```bash
   python -m uvicorn app.main:app --reload --port 8001
   ```

### Frontend Setup

1. **Copy environment variables:**
   ```bash
   cd frontend
   cp .env.example .env.local
   ```

2. **Edit `.env.local` with InsForge credentials:**
   ```
   NEXT_PUBLIC_INSFORGE_URL=https://your-project.us-east.insforge.app
   NEXT_PUBLIC_INSFORGE_ANON_KEY=your-anon-key
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
   ```

3. **Get the anon key via CLI:**
   ```bash
   npx @insforge/cli secrets get ANON_KEY
   ```

4. **Install dependencies:**
   ```bash
   npm install
   ```

5. **Run frontend:**
   ```bash
   npm run dev
   ```

6. **Open browser:**
   ```
   http://localhost:3000
   ```

## Database Schema (InsForge)

The following table needs to be created in InsForge. Use the `insforge-cli` skill to set up the schema:

```sql
CREATE TABLE investigations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  namespace VARCHAR(255),
  root_cause TEXT NOT NULL,
  explanation TEXT,
  confidence INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'pending',
  diagnosis_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable row-level security
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

-- RLS policy: users can only see their own investigations
CREATE POLICY "Users can see their own investigations" ON investigations
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS policy: users can only insert their own investigations
CREATE POLICY "Users can insert their own investigations" ON investigations
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Index for common queries
CREATE INDEX idx_investigations_user_created 
  ON investigations(user_id, created_at DESC);
```

## User Flow

### 1. Login
- User visits `http://localhost:3000`
- Redirected to `/login` if not authenticated
- Can sign up or sign in with email/password
- Credentials stored in InsForge auth

### 2. Investigate
- Click "Investigate Cluster" button
- Real-time progress updates shown
- Backend runs Kubernetes investigation
- AI generates diagnosis with root cause

### 3. View Results
- Root cause displayed prominently
- Confidence score with visual indicator
- Suggested fixes and kubectl commands
- Investigation saved to history

### 4. View History
- Investigation history table shows past investigations
- Sorted by most recent first
- Shows confidence score and status
- Only displays user's own investigations (RLS)

## Features

### Authentication
- ✅ Sign up / Sign in with email/password
- ✅ Protected dashboard (redirect to login if unauthenticated)
- ✅ Auto-logout on sign out
- ✅ Session persistence

### Investigation Dashboard
- ✅ Investigate Cluster button
- ✅ Real-time progress display with 7 investigation steps
- ✅ Animated step completion
- ✅ Root cause diagnosis card
- ✅ Confidence score with progress bar
- ✅ kubectl command suggestions
- ✅ Investigation history table
- ✅ Minimal, professional UI

### Backend Integration
- ✅ Authentication header handling
- ✅ User context extraction from JWT
- ✅ Investigation history storage
- ✅ Error handling and fallbacks

### Real-time Capabilities (Foundation)
- ✅ InsForge realtime SDK integrated
- ✅ `useInvestigationProgress` hook ready for real-time updates
- ✅ Channel subscription pattern implemented
- ✅ Ready for backend-published progress events

## API Endpoints

### POST /investigate
Trigger a new investigation.

**Request:**
```json
{
  "namespace": "default"  // optional
}
```

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response:**
```json
{
  "status": "success",
  "investigation": { /* evidence */ },
  "diagnosis": {
    "root_cause": "DATABASE_URL missing",
    "explanation": "...",
    "fix": "Add missing environment variable",
    "kubectl_commands": ["kubectl edit deployment..."],
    "confidence": 92
  }
}
```

### GET /investigations/history
Fetch investigation history for authenticated user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "...",
      "root_cause": "...",
      "confidence": 92,
      "created_at": "2024-01-15T10:30:00Z",
      "status": "success"
    }
  ]
}
```

## Production Deployment

### Database Migrations
After database schema creation, deploy to production:

```bash
npx @insforge/cli database migrations deploy
```

### Backend Deployment
Deploy FastAPI backend to your hosting (Railway, Render, etc.):
```bash
# Add INSFORGE_URL and INSFORGE_API_KEY to production secrets
git push heroku main  # or equivalent for your platform
```

### Frontend Deployment
Deploy Next.js to Vercel:
```bash
vercel deploy --prod
# Update environment variables in Vercel dashboard
```

## Troubleshooting

### "InsForge credentials missing"
- Ensure `.env.local` has `NEXT_PUBLIC_INSFORGE_URL` and `NEXT_PUBLIC_INSFORGE_ANON_KEY`
- Restart dev server after updating `.env.local`

### "Failed to fetch history"
- Check backend is running on port 8001
- Verify `NEXT_PUBLIC_API_BASE_URL` is correct
- Check browser console for CORS errors

### API returns 401
- JWT token may be expired
- User session lost
- Refresh page and re-login

### Database queries fail
- Ensure database migrations ran: `npx @insforge/cli database migrations deploy`
- Check RLS policies are enabled
- Verify user_id in JWT matches

## Next Steps

1. **Schema Creation**: Use InsForge CLI to create the `investigations` table with RLS policies
2. **Environment Setup**: Add InsForge credentials to `.env` and `.env.local`
3. **Start Development**: Run backend and frontend servers
4. **Test Login Flow**: Sign up, log in, and access protected dashboard
5. **Test Investigation**: Click "Investigate Cluster" and verify API integration
6. **Customize**: Adjust investigation steps, UI styling, or add more features

## Resources

- [InsForge Documentation](https://insforge.dev)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Tailwind CSS](https://tailwindcss.com/docs)

## Support

For issues with:
- **InsForge**: Use `npx @insforge/cli feedback` or check docs
- **Frontend**: Check browser console for errors
- **Backend**: Check terminal output and application logs
