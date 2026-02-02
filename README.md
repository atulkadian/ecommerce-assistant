# E-Commerce Shopping Assistant

An AI-powered shopping assistant built with FastAPI, LangGraph, and Next.js that helps users discover products through natural language conversations.

## Features

- AI-powered product discovery using Google Gemini
- Real-time streaming responses with Server-Sent Events
- Persistent shopping cart with database storage
- Persistent chat and conversation history cart with database storage
- Responsive design for mobile, tablet, and desktop
- Dark/light theme support
- Rate limiting
- Fun snowfall animation toggle

## Tech Stack

**Backend:**

- FastAPI 0.109.0 - REST API framework
- LangGraph 0.2.55 - Agent orchestration
- LangChain 0.3.12 - LLM integration
- Google Gemini 2.5 Flash Lite - Language model
- SQLAlchemy 2.0.23 - ORM
- SQLite - Database
- SlowAPI - Rate limiting

**Frontend:**

- Next.js 14.1.0 - React framework
- TypeScript - Type safety
- TailwindCSS - Styling
- react-markdown - Message rendering
- next-themes - Theme management

## Quick Start

### Prerequisites

- Docker and Docker Compose (optional)
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/atulkadian/ecommerce-assistant
cd ecommerce-assistant
```

2. **Configure environment**

```bash
# Create backend .env file
echo "GOOGLE_API_KEY=your-api-key-here" > backend/.env
echo "FAKE_STORE_API_URL=https://fakestoreapi.com" >> backend/.env
```

3. **Run with Docker**

```bash
docker compose up
```

4. **Run without Docker**

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The applications will be available at:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Design Decisions

### 1. **Streaming Responses**

- Uses Server-Sent Events (SSE) for real-time streaming
- Provides immediate feedback with typewriter effect
- Improves perceived performance

### 2. **Lazy Conversation Creation**

- Conversations created after first LLM response, not on initial request
- Prevents empty conversations on API failures
- Auto-generates titles from first user message

### 3. **Context Variables for DB Session**

- Uses Python `ContextVar` to pass database session to tools
- Allows tools to access database without explicit parameter passing
- Enables proper transaction management

### 4. **Database Persistence Strategy**

- Bind mount (`./backend/data:/app/data`) for host visibility
- SQLAlchemy's `expire_all()` ensures fresh queries
- Supports both conversations and shopping cart

### 5. **Rate Limiting**

- 20 req/min for chat endpoints (resource-intensive)
- 60 req/min for read operations
- 30 req/min for write operations
- Protects against abuse while allowing normal usage

### 6. **Category Normalization**

- Maps user-friendly terms to exact API categories
- Example: "men", "mens", "men's" should mean "men's clothing"
- Improves user experience with flexible input

### 7. **Responsive Design**

- Mobile-first approach with Tailwind breakpoints
- Sidebar auto-closes on mobile, stays open on desktop
- Touch-friendly UI elements

## API Endpoints

| Endpoint              | Method | Description         | Rate Limit |
| --------------------- | ------ | ------------------- | ---------- |
| `/chat/stream`        | POST   | Stream AI responses | 20/min     |
| `/conversations`      | GET    | List conversations  | 60/min     |
| `/conversations/{id}` | GET    | Get conversation    | 60/min     |
| `/conversations`      | POST   | Create conversation | 30/min     |
| `/conversations/{id}` | DELETE | Delete conversation | 30/min     |

## Environment Variables

**Backend:**

- `GOOGLE_API_KEY` - Google Gemini API key (required)
- `FAKE_STORE_API_URL` - Product API URL (default: https://fakestoreapi.com)
- `DATABASE_URL` - SQLite database path (auto-configured)

**Frontend:**

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## License

MIT
