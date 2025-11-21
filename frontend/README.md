# SOAP Evaluation Dashboard Frontend

Modern React + TypeScript dashboard for exploring SOAP note evaluation results.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

## Configuration

The API base URL can be configured via environment variable:

Create a `.env.local` file:
```
VITE_API_BASE_URL=http://localhost:8000
```

By default, it uses `http://localhost:8000` (the FastAPI backend).

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── SummaryMetrics.tsx
│   │   ├── NotesList.tsx
│   │   └── NoteDetail.tsx
│   ├── api.ts          # API client functions
│   ├── config.ts       # Configuration
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── index.html
└── package.json
```

