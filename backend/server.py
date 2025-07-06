from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import logging
from jinja2 import Template
import uuid
import asyncio
import pandas as pd
import io

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Automatic Email Sender", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "hackfinity.innovation@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "dudv vevw kmkm oqxm"),
    MAIL_FROM=os.getenv("MAIL_FROM", "hackfinity.innovation@gmail.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# MongoDB setup
try:
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client.email_sender_db
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    db = None

# Scheduler setup
jobstores = {
    'default': MemoryJobStore()
}
executors = {
    'default': ThreadPoolExecutor(20)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="UTC"
)

try:
    scheduler.start()
    logger.info("Scheduler started successfully")
except Exception as e:
    logger.error(f"Failed to start scheduler: {e}")

# Pydantic models
class EmailContext(BaseModel):
    name: str = "Valued Customer"
    offer: str = "Special Offer"
    custom_message: str = ""

class PersonalizedEmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    email_body: str
    schedule_time: Optional[datetime] = None

class SingleEmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    context: EmailContext
    template: str = ""
    schedule_time: Optional[datetime] = None

class BulkEmailRequest(BaseModel):
    recipients: List[EmailStr]
    subject: str
    contexts: List[EmailContext]
    template: str = ""
    schedule_time: Optional[datetime] = None

class ExcelColumnMapping(BaseModel):
    email_column: str
    subject_column: str
    body_column: str
    name_column: Optional[str] = None

class ExcelEmailData(BaseModel):
    email: str
    subject: str
    body: str
    name: Optional[str] = None

class ExcelBulkEmailRequest(BaseModel):
    emails: List[ExcelEmailData]
    schedule_time: Optional[datetime] = None

# Default email template - Simple Plain Text
DEFAULT_TEMPLATE = """Hi {{ context.name }},

{{ context.custom_message }}

{% if context.offer %}
{{ context.offer }}
{% endif %}

Best regards,
{{ sender_name }}
{{ sender_email }}
{% if sender_phone %}
{{ sender_phone }}
{% endif %}"""

# Email utility functions
async def render_email_template(template_str: str, context: Dict[str, Any]) -> str:
    """Render email template with context"""
    try:
        template = Template(template_str)
        
        # Add sender information and current time
        context.update({
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            'sender_name': "The Team",
            'sender_email': "hackfinity.innovation@gmail.com",
            'sender_phone': "+91 7418400160"
        })
        
        return template.render(context)
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        # Return simple fallback
        context_data = context.get('context', {})
        return f"""Hi {context_data.get('name', 'Valued Customer')},

{context_data.get('custom_message', 'Thank you for your interest.')}

{context_data.get('offer', '')}

Best regards,
The Team
hackfinity.innovation@gmail.com
+91 7418400160"""

async def send_personalized_email(recipient: str, subject: str, email_body: str) -> bool:
    """Send a personalized email with custom body content"""
    try:
        # Create message with plain text/HTML body
        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=email_body,
            subtype="html" if "<" in email_body and ">" in email_body else "plain"
        )
        
        # Send email
        fm = FastMail(conf)
        await fm.send_message(message)
        
        logger.info(f"Personalized email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send personalized email to {recipient}: {e}")
        return False

async def send_single_email(recipient: str, subject: str, context: EmailContext, template: str = "") -> bool:
    """Send a single email"""
    try:
        # Use custom template or default
        email_template = template if template.strip() else DEFAULT_TEMPLATE
        
        # Render template
        plain_content = await render_email_template(email_template, {
            'subject': subject,
            'context': context.dict()
        })
        
        # Create message
        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=plain_content,
            subtype="plain"
        )
        
        # Send email
        fm = FastMail(conf)
        await fm.send_message(message)
        
        logger.info(f"Email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False

async def send_bulk_emails(recipients: List[str], subject: str, contexts: List[EmailContext], template: str = "") -> List[Dict]:
    """Send bulk emails with individual contexts"""
    results = []
    
    for i, recipient in enumerate(recipients):
        # Use corresponding context or first one as default
        context = contexts[i] if i < len(contexts) else contexts[0]
        
        success = await send_single_email(recipient, subject, context, template)
        results.append({
            "recipient": recipient,
            "success": success,
            "context": context.dict()
        })
        
        # Add small delay to avoid overwhelming SMTP server
        await asyncio.sleep(0.5)
    
    return results

# Scheduled email function
async def scheduled_email_job(recipient: str, subject: str, context: EmailContext, template: str, job_id: str):
    """Job function for scheduled emails"""
    try:
        success = await send_single_email(recipient, subject, context, template)
        
        # Log to database
        if db is not None:
            await db.email_logs.insert_one({
                "job_id": job_id,
                "recipient": recipient,
                "subject": subject,
                "context": context.dict(),
                "sent_at": datetime.utcnow(),
                "success": success,
                "type": "scheduled"
            })
        
        logger.info(f"Scheduled email job {job_id} completed for {recipient}")
        
    except Exception as e:
        logger.error(f"Scheduled email job {job_id} failed: {e}")

# API Endpoints
@app.get("/api/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Automatic Email Sender API</title></head>
        <body>
            <h1>🚀 Automatic Email Sender API</h1>
            <p>Your Gmail SMTP email sender is running!</p>
            <p><a href="/docs">📚 View API Documentation</a></p>
            <p><strong>Configured Email:</strong> hackfinity.innovation@gmail.com</p>
        </body>
    </html>
    """

@app.post("/api/send-personalized-email")
async def send_personalized_email_now(request: PersonalizedEmailRequest):
    """Send a personalized email with custom body content immediately"""
    try:
        success = await send_personalized_email(
            request.recipient,
            request.subject,
            request.email_body
        )
        
        # Log to database
        if db is not None:
            await db.email_logs.insert_one({
                "recipient": request.recipient,
                "subject": request.subject,
                "email_body": request.email_body,
                "sent_at": datetime.utcnow(),
                "success": success,
                "type": "personalized_immediate"
            })
        
        if success:
            return {"status": "success", "message": f"Personalized email sent successfully to {request.recipient}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send personalized email")
            
    except Exception as e:
        logger.error(f"Send personalized email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule-personalized-email")
async def schedule_personalized_email_endpoint(request: PersonalizedEmailRequest):
    """Schedule a personalized email with custom body content for later delivery"""
    if not request.schedule_time:
        raise HTTPException(status_code=400, detail="Schedule time is required")
    
    if request.schedule_time <= datetime.now():
        raise HTTPException(status_code=400, detail="Schedule time must be in the future")
    
    job_id = f"personalized_email_{uuid.uuid4().hex[:8]}"
    
    try:
        # Schedule the job
        scheduler.add_job(
            send_personalized_email,
            trigger="date",
            run_date=request.schedule_time,
            args=[request.recipient, request.subject, request.email_body],
            id=job_id,
            replace_existing=True
        )
        
        # Store in database
        if db is not None:
            await db.scheduled_emails.insert_one({
                "job_id": job_id,
                "recipient": request.recipient,
                "subject": request.subject,
                "email_body": request.email_body,
                "schedule_time": request.schedule_time,
                "status": "scheduled",
                "created_at": datetime.utcnow(),
                "type": "personalized"
            })
        
        return {
            "status": "success",
            "message": f"Personalized email scheduled successfully for {request.schedule_time}",
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"Schedule personalized email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send-email")
async def send_email_now(request: SingleEmailRequest):
    """Send a single email immediately"""
    try:
        success = await send_single_email(
            request.recipient,
            request.subject,
            request.context,
            request.template
        )
        
        # Log to database
        if db is not None:
            await db.email_logs.insert_one({
                "recipient": request.recipient,
                "subject": request.subject,
                "context": request.context.dict(),
                "sent_at": datetime.utcnow(),
                "success": success,
                "type": "immediate"
            })
        
        if success:
            return {"status": "success", "message": f"Email sent successfully to {request.recipient}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        logger.error(f"Send email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send-bulk-email")
async def send_bulk_email_now(request: BulkEmailRequest):
    """Send bulk emails immediately"""
    try:
        results = await send_bulk_emails(
            request.recipients,
            request.subject,
            request.contexts,
            request.template
        )
        
        # Log to database
        if db is not None:
            await db.email_logs.insert_one({
                "recipients": request.recipients,
                "subject": request.subject,
                "contexts": [ctx.dict() for ctx in request.contexts],
                "sent_at": datetime.utcnow(),
                "results": results,
                "type": "bulk_immediate"
            })
        
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        return {
            "status": "success",
            "message": f"Bulk email completed: {successful}/{total} sent successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Bulk email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule-email")
async def schedule_email_endpoint(request: SingleEmailRequest):
    """Schedule a single email for later delivery"""
    if not request.schedule_time:
        raise HTTPException(status_code=400, detail="Schedule time is required")
    
    if request.schedule_time <= datetime.now():
        raise HTTPException(status_code=400, detail="Schedule time must be in the future")
    
    job_id = f"email_{uuid.uuid4().hex[:8]}"
    
    try:
        # Schedule the job
        scheduler.add_job(
            scheduled_email_job,
            trigger="date",
            run_date=request.schedule_time,
            args=[request.recipient, request.subject, request.context, request.template, job_id],
            id=job_id,
            replace_existing=True
        )
        
        # Store in database
        if db is not None:
            await db.scheduled_emails.insert_one({
                "job_id": job_id,
                "recipient": request.recipient,
                "subject": request.subject,
                "context": request.context.dict(),
                "template": request.template,
                "schedule_time": request.schedule_time,
                "status": "scheduled",
                "created_at": datetime.utcnow(),
                "type": "single"
            })
        
        return {
            "status": "success",
            "message": f"Email scheduled successfully for {request.schedule_time}",
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"Schedule email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scheduled-emails")
async def get_scheduled_emails():
    """Get all scheduled emails"""
    try:
        if db is not None:
            cursor = db.scheduled_emails.find({"status": "scheduled"})
            emails = await cursor.to_list(100)
            
            # Convert ObjectId to string for JSON serialization
            for email in emails:
                email["_id"] = str(email["_id"])
                
            return {"scheduled_emails": emails}
        else:
            return {"scheduled_emails": []}
        
    except Exception as e:
        logger.error(f"Get scheduled emails error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email-logs")
async def get_email_logs(limit: int = 50):
    """Get email sending logs"""
    try:
        if db is not None:
            cursor = db.email_logs.find().sort("sent_at", -1).limit(limit)
            logs = await cursor.to_list(limit)
            
            # Convert ObjectId to string for JSON serialization
            for log in logs:
                log["_id"] = str(log["_id"])
                
            return {"logs": logs}
        else:
            return {"logs": []}
        
    except Exception as e:
        logger.error(f"Get email logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "email_configured": conf.MAIL_USERNAME is not None,
        "database_connected": db is not None,
        "scheduler_running": scheduler.running
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)