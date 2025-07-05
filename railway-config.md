# Railway Deployment Configuration

# 1. Create account at railway.app
# 2. Connect GitHub repository  
# 3. Select backend folder
# 4. Railway will auto-detect Python and deploy

# Procfile for Railway (create this file in backend folder)
web: uvicorn server:app --host 0.0.0.0 --port $PORT