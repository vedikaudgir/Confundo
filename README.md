# Chat Meme Generator

Chat Meme Generator is a full-stack web application that generates platform-style chat screenshots from structured message data. It implements a custom rendering engine to simulate real messaging interfaces such as WhatsApp and ChatGPT with accurate layout, typography, and visual structure.

---

## Overview

The application allows users to create chats, add messages, customize participants, and generate realistic chat previews as images. The system is designed with a modular backend architecture and a rendering pipeline that converts chat data into platform-specific UI representations.

---

## Features

- Dynamic chat creation and message management  
- Platform-specific rendering (WhatsApp-style, ChatGPT-style, Instagram DM(yet to come))  
- Custom layout engine with text wrapping, alignment, and spacing logic  
- Avatar upload and participant handling  
- Image generation using server-side rendering  
- Real-time preview updates  
- Deployed frontend and backend with production configuration  

---

## Architecture

The backend follows a layered design:

- Schemas: Data validation and request/response models  
- Services: Core business logic and rendering workflows  
- Repositories: Data access and persistence  
- Rendering Layer: Converts structured chat data into images using PIL  

Frontend communicates with the backend via REST APIs.

---

## Tech Stack

### Frontend
- React  
- Vite
- Tailwind 3
- Vercel  

### Backend
- FastAPI  
- Python  
- Pillow (PIL) for Image Generation.

### Infrastructure
- Docker  
- Railway  
- REST API  

---

## Rendering Engine

The core of the application is a custom-built rendering engine that:

- Calculates dynamic bubble sizes based on text length  
- Handles multi-line text wrapping and alignment  
- Positions timestamps intelligently  
- Simulates platform-specific UI elements (headers, icons, input bars)  
- Supports extensibility for additional chat platforms  

---

## API Endpoints

POST /chats  
PATCH /chats/{chat_id}  
POST /chats/{chat_id}/messages  
GET /chats/{chat_id}/preview  
POST /participants/{participant_id}/avatar  

---

## Setup

### Backend

```bash
cd server
pip install -r requirements.txt
uvicorn utils.main:app --reload
```

### Frontend

```bash
cd client
npm install
npm run dev
```

---

## Deployment

- Frontend deployed on Vercel  
- Backend containerized with Docker and deployed on Railway
- <a>https://chat-meme-generator.vercel.app/</a>

---

## Working Model

<img width="1920" height="1080" alt="{4461B342-2A0E-40F5-AF0B-A3DC76D965E1}" src="https://github.com/user-attachments/assets/0317059e-8ba2-4ff9-8745-0084949d6c2c" />


## Future Improvements

- Additional platform renderers (Instagram, iMessage)  
- Markdown and rich-text support  
- CDN-based image delivery  
- Background processing for rendering  
- Authentication system  

---

## Author

Vedika Udgir
