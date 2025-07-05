# Free Hosting Deployment Guide for Auto-Email App

## Architecture Overview
- Frontend: React app → Netlify (Free)
- Backend: FastAPI → Railway (Free tier)  
- Database: MongoDB → MongoDB Atlas (Free tier)

## Required Files for Deployment

### Frontend Deployment (Netlify)
1. Build the React app
2. Upload build folder to Netlify
3. Configure environment variables

### Backend Deployment (Railway)
1. Create requirements.txt
2. Create Procfile or railway.json
3. Configure environment variables
4. Deploy FastAPI app

### Database Setup (MongoDB Atlas)
1. Create free cluster
2. Get connection string
3. Update backend configuration

## Environment Variables Needed
- MONGO_URL (from MongoDB Atlas)
- MAIL_USERNAME, MAIL_PASSWORD (Gmail SMTP)
- REACT_APP_BACKEND_URL (Railway backend URL)

## Cost: $0 per month (Free tiers)