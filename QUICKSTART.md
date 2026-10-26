# AI Kubernetes Agent - Quick Start Guide

## 1. Project Initialization

### InsForge Project Setup
```bash
# Link existing project
npx @insforge/cli link

# Or create new project
npx @insforge/cli create ai-kube-project
```

### Get Credentials
```bash
# Get anon key for frontend
npx @insforge/cli secrets get ANON_KEY

# Get API key for backend
npx @insforge/cli secrets get API_KEY

# Get InsForge URL
cat .insforge/project.json | grep oss_host
```

## 2. Backend Setup (FastAPI)

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env with your InsForge credentials
# INSFORGE_URL=https://your-project.us-east.insforge.app
# INSFORGE_API_KEY=your-api-key
# OPENROUTER_API_KEY=your-openrouter-key

# Install dependencies
pip install -r requirements.txt

# Run backend on port 8001
python -m uvicorn app.main:app --reload --port 8001
```

## 3. Frontend Setup (Next.js)

```bash
cd frontend

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your InsForge credentials
# NEXT_PUBLIC_INSFORGE_URL=https://your-project.us-east.insforge.app
# NEXT_PUBLIC_INSFORGE_ANON_KEY=your-anon-key
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Install dependencies
npm install

# Run frontend on port 3000
npm run dev
```

## 4. Create Database Schema

Run this SQL in InsForge to create the investigations table with RLS:

```bash
npx @insforge/cli database sql --exec "
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

ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

CREATE POLICY 'Users can see their own investigations' ON investigations
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY 'Users can insert their own investigations' ON investigations
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE INDEX idx_investigations_user_created 
  ON investigations(user_id, created_at DESC);
"
```

## 5. Open Application

1. **Frontend**: http://localhost:3000
2. **Backend API**: http://localhost:8001
3. **API Docs**: http://localhost:8001/docs

## 6. Test the Flow

### Sign Up
1. Click "Don't have an account? Sign up"
2. Enter email and password
3. Click Sign Up

### Sign In
1. Enter email and password
2. Click Sign In

### Run Investigation
1. Click "Investigate Cluster" button
2. Watch real-time progress (7 steps)
3. View diagnosis results
4. Check confidence score

### View History
1. Scroll down to Investigation History
2. See past investigations (empty initially)
3. Run more investigations to populate

## Key Components

### Frontend Pages
- `/` - Dashboard (protected, requires login)
- `/login` - Authentication (sign up/sign in)

### Frontend Components
- `Dashboard` - Main app shell with all sections
- `InvestigateButton` - Trigger investigation
- `InvestigationProgress` - Show progress steps
- `RootCauseCard` - Display diagnosis
- `InvestigationHistory` - Show past investigations
- `AuthProvider` - Handle authentication state

### Backend Endpoints
- `POST /investigate` - Run investigation
- `GET /investigations/history` - Fetch history
- `GET /health` - Health check

## Environment Files

### Backend (.env)
```
INSFORGE_URL=https://xxx.us-east.insforge.app
INSFORGE_API_KEY=xxx
OPENROUTER_API_KEY=xxx
OPENROUTER_MODEL=openai/gpt-4o-mini
KUBECONFIG_PATH=/root/.kube/config
KUBECTL_BIN=kubectl
KUBECTL_TIMEOUT_SECONDS=30
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_INSFORGE_URL=https://xxx.us-east.insforge.app
NEXT_PUBLIC_INSFORGE_ANON_KEY=xxx
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

## Troubleshooting

### Port Already in Use
```bash
# Find process on port 8001 (backend)
lsof -i :8001
kill -9 <PID>

# Find process on port 3000 (frontend)
lsof -i :3000
kill -9 <PID>
```

### InsForge Credentials Error
1. Verify credentials in `.env` and `.env.local`
2. Restart dev servers after updating
3. Check `.insforge/project.json` exists

### Sign In Not Working
1. Check browser console for errors
2. Verify InsForge URL is correct
3. Check network tab for failed requests
4. Ensure user was created in sign up

### History Not Loading
1. Check backend is running on 8001
2. Verify database schema created
3. Check browser console for API errors
4. Run investigation first to create data

## Next Steps

1. ✅ Login/Authentication
2. ✅ Dashboard UI
3. ✅ Investigation Progress
4. ✅ Root Cause Display
5. ✅ Investigation History
6. ⏭️ Real-time Updates (foundation ready)
7. ⏭️ Production Deployment

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Login Page                                       │ │
│  │ - Sign Up / Sign In (InsForge Auth)             │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Dashboard (Protected)                           │ │
│  │ - Investigate Button (POST /investigate)        │ │
│  │ - Progress Display (animated)                   │ │
│  │ - Diagnosis Card                                │ │
│  │ - History Table (GET /investigations/history)   │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                          ↓ (Auth Header)
┌─────────────────────────────────────────────────────┐
│                Backend (FastAPI)                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │ POST /investigate                               │ │
│  │ - Run Kubernetes investigation                  │ │
│  │ - AI Analysis                                   │ │
│  │ - Save to history (InsForge DB)                 │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │ GET /investigations/history                     │ │
│  │ - Query user investigations                     │ │
│  │ - Return with RLS applied                       │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           InsForge Backend                          │
│  - Auth (JWT)                                       │
│  - PostgreSQL Database                              │
│  - RLS Policies                                     │
│  - Real-time Channels                               │
└─────────────────────────────────────────────────────┘
```

## Support & Resources

- **InsForge CLI**: `npx @insforge/cli --help`
- **FastAPI Docs**: http://localhost:8001/docs
- **Next.js Dev**: npm run dev
- **Logs**: Check terminal output and browser console
