# Confundo client

The React/Vite frontend connects to the FastAPI API for cookie-based authentication, account settings, owner-scoped chats and messages, Pillow-generated images, and private generation history. Set `VITE_API_BASE_URL` before starting the dev server; it defaults to `http://localhost:8000` in development and `/api` in production. Vercel rewrites `/api/*` to the Render API so production session cookies remain first-party.

For production, configure the Vercel project with `VITE_API_BASE_URL=/api` (or leave it unset) and the Render service with `APP_ENV=production`, `CORS_ALLOW_ORIGINS=https://confundo.vercel.app`, a persistent `DATABASE_URL`, and a stable `JWT_SECRET_KEY` of at least 32 bytes. Keep `COOKIE_SECURE=true` and `COOKIE_SAMESITE=none` (the production defaults), and leave `COOKIE_DOMAIN` unset so the API uses host-only cookies. Build/redeploy the backend before the frontend so the API exposes the CSRF response header before the client depends on it. Do not configure the frontend to call the Render host directly in production; that reintroduces cross-site cookie restrictions.

Routes include the landing page, fictional examples, protected generator and account pages, login/signup, password-help information, and terms/privacy/cookie/FAQ/about pages. Email-based password reset is not available because no email-delivery or reset-token backend is configured.

For complete PowerShell setup, migration, API and frontend startup, production configuration, and test commands, see the repository [README](../README.md).
