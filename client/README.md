# ChattieBaby client

The React/Vite frontend connects to the FastAPI API for cookie-based authentication, account settings, owner-scoped chats and messages, Pillow-generated images, and private generation history. Set `VITE_API_BASE_URL` to the API origin before starting the dev server; it defaults to the existing deployed API.

Routes include the landing page, fictional examples, protected generator and account pages, login/signup, password-help information, and terms/privacy/cookie/FAQ/about pages. Email-based password reset is not available because no email-delivery or reset-token backend is configured.

For complete PowerShell setup, migration, API and frontend startup, production configuration, and test commands, see the repository [README](../README.md).
