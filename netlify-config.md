# Netlify Deployment Steps

# 1. Build React app locally
cd /app/frontend
yarn build

# 2. Upload to Netlify
# - Go to netlify.com
# - Drag and drop the 'build' folder
# - Or connect GitHub repository

# 3. Configure environment variables in Netlify:
REACT_APP_BACKEND_URL=https://yourapp.railway.app

# 4. Set build settings (if using GitHub):
Build command: yarn build
Publish directory: build