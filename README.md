---
title: EmpManager Pro
emoji: 🏢
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# EmpManager Pro - AI HR Suite

A comprehensive Employee Management System with AI-powered insights, RAG Chatbot, and Voice Agent.

## Setup for Hugging Face Spaces
This app is configured to run on Hugging Face Spaces using Docker.

### Environment Variables Required:
Ensure you add the following secrets in your Space settings:
- `SECRET_KEY`: A secure random string
- `DATABASE_URL`: Your Supabase connection string (PostgreSQL)
- `GROQ_API_KEY`: For the RAG Chatbot
- `TWILIO_ACCOUNT_SID`: For the Voice Agent
- `TWILIO_AUTH_TOKEN`: For the Voice Agent
- `TWILIO_PHONE_NUMBER`: For the Voice Agent

### Local Development
1. Clone the repo
2. Create a `.env` file from `.env.example`
3. Run `pip install -r requirements.txt`
4. Run `py app.py`
