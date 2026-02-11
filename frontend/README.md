# Exactius Frontend

Next.js 14 frontend for the Exactius multi-account Meta ads automation platform.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (Radix UI primitives)
- **State Management:**
  - React Query (TanStack Query v5) - Server state
  - Zustand - Client state
- **Form Management:** React Hook Form + Zod
- **HTTP Client:** Axios
- **Icons:** Lucide React

## Project Structure

```
frontend/
├── src/
│   ├── app/                     # Next.js App Router
│   │   ├── (dashboard)/         # Dashboard route group
│   │   │   ├── accounts/        # Accounts list page
│   │   │   ├── campaigns/       # Campaign pages
│   │   │   ├── layout.tsx       # Dashboard layout
│   │   │   └── page.tsx         # Dashboard home
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Root redirect
│   │   └── globals.css          # Global styles
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── accounts/            # Account components
│   │   └── layout/              # Layout components (Sidebar, Header)
│   ├── lib/
│   │   ├── api/                 # API client layer
│   │   │   ├── client.ts        # Base Axios client
│   │   │   ├── accounts.ts      # Account endpoints
│   │   │   └── campaigns.ts     # Campaign endpoints
│   │   ├── hooks/               # React hooks
│   │   │   ├── useAccounts.ts   # Account queries
│   │   │   └── useCampaigns.ts  # Campaign mutations
│   │   ├── providers/           # React providers
│   │   │   └── QueryProvider.tsx
│   │   └── utils/               # Utilities
│   └── types/
│       └── api.ts               # TypeScript types
└── public/                      # Static assets
```

## Environment Variables

Create a `.env.local` file:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_BATCH=true
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

## Getting Started

### Prerequisites

- Node.js 20+ (LTS)
- npm 10+
- FastAPI backend running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Development

### Run Development Server

```bash
npm run dev
```

### Run with Backend

To run both frontend and backend concurrently:

```bash
# From project root
cd frontend && npm run dev

# In another terminal
cd .. && ./scripts/start_api.sh
```

### Build for Production

```bash
npm run build
npm start
```

### Lint and Format

```bash
# Run ESLint
npm run lint

# Format with Prettier
npx prettier --write .
```

## Features Implemented

### Phase 3 - Initial Setup ✅

- [x] Next.js 14 project with TypeScript
- [x] Tailwind CSS + shadcn/ui components
- [x] React Query integration
- [x] API client layer (Axios + TypeScript types)
- [x] Dashboard layout (Sidebar + Header)
- [x] Accounts list page with AccountCard components
- [x] Dashboard home page with stats

### Next Steps

Phase 3 - Campaign Builder:
- [ ] Campaign wizard component (6-step flow)
- [ ] Asset preview component
- [ ] Real-time progress tracking
- [ ] Campaign history page
- [ ] Batch operations interface
- [ ] Zustand store for wizard state

## Available Pages

- **`/`** - Dashboard home (stats, quick actions, getting started guide)
- **`/accounts`** - Client accounts list
- **`/campaigns/create`** - Campaign builder wizard (TODO)
- **`/campaigns/history`** - Campaign history (TODO)

## API Integration

The frontend integrates with the FastAPI backend at `http://localhost:8000`:

### Account Endpoints
- `GET /api/accounts/` - List all accounts
- `GET /api/accounts/{id}` - Get account details
- `GET /api/accounts/{id}/validate` - Validate account
- `GET /api/accounts/{id}/campaign-types` - Get campaign types

### Campaign Endpoints
- `POST /api/campaigns/preview` - Preview campaign (dry-run)
- `POST /api/campaigns/launch` - Launch campaign

## Deployment (Google Cloud Run)

### Build Docker Image

```bash
# Build with Next.js standalone output
npm run build

# Build Docker image
docker build -t gcr.io/PROJECT_ID/exactius-frontend .
```

### Deploy to Cloud Run

```bash
# Push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/exactius-frontend

# Deploy to Cloud Run
gcloud run deploy exactius-frontend \
  --image gcr.io/PROJECT_ID/exactius-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=https://exactius-backend-xxx.run.app
```

## Troubleshooting

### API Connection Issues

If you see "Cannot connect to server" errors:

1. Ensure the FastAPI backend is running: `http://localhost:8000/health`
2. Check CORS configuration in `src/api/main.py`
3. Verify `NEXT_PUBLIC_API_URL` in `.env.local`

### Type Errors

If you encounter TypeScript errors:

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## Contributing

See main project [CLAUDE.md](../CLAUDE.md) for development guidelines.

---

**Built with Claude Sonnet 4.5**
