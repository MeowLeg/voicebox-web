# OpenCode Agent Instructions

## Project Overview

Next.js + Tailwind frontend for Voicebox TTS API. Uses Next.js App Router with src/ directory structure.

## Voicebox API (localhost:17493)

Backend is a FastAPI server. Interactive docs at `http://localhost:17493/docs`.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server health check |
| GET | `/profiles` | List voice profiles |
| POST | `/generate` | Generate speech from text |
| GET | `/audio/{id}` | Serve generated audio file |
| GET | `/generate/{id}/status` | Poll generation status |

### POST /generate Request Schema

```json
{
  "profile_id": "uuid",
  "text": "Text to synthesize",
  "language": "en",
  "seed": 42,
  "model_size": "1.7B",
  "instruct": "Speak clearly"
}
```

### Response Schema

```json
{
  "id": "generation_uuid",
  "profile_id": "profile_uuid",
  "text": "Text to synthesize",
  "language": "en",
  "audio_path": "/path/to/audio.wav",
  "duration": 3.5,
  "seed": 42,
  "instruct": "Speak clearly",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Architecture

- Next.js 16 App Router with `src/` directory
- Tailwind CSS v4 for styling
- API calls go through Next.js `/api/proxy` routes (not direct to backend)
- Audio files served via `/api/proxy/audio?path=audio/{id}`
- Frontend polls `/api/proxy?path=generate/{id}/status` for completion

## Available Commands

```bash
npm run dev      # Start dev server (http://localhost:3000)
npm run build    # Production build
npm run start    # Start production server
npm run lint     # Run ESLint
```

## Important Notes

- Backend must be running before testing generation features
- First generation is slow (model initialization), subsequent calls are faster
- Generated audio is saved on backend and accessible via `/audio/{id}`
- Voice profiles must exist on backend before generating speech
- No authentication required (local-first app)
- Use `splitText()` from `src/lib/api.ts` to chunk long text (500 char segments)
- Use `concatWavBlobs()` to merge multiple WAV segments
