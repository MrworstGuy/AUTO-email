import requests
import unittest
import json
from datetime import datetime, timedelta
import time

class EmailSenderAPITest(unittest.TestCase):
    """Test suite for the Automatic Email Sender API"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Use the public endpoint from frontend/.env
        self.base_url = "https://82ef2375-69f0-4164-b680-2a670cae9a8d.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.test_email = "test@example.com"  # Use a test email that won't actually receive emails
        
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.api_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue("email_configured" in data)
        self.assertTrue("database_connected" in data)
        self.assertTrue("scheduler_running" in data)
        print("✅ Health endpoint test passed")
        
    def test_send_single_email(self):
        """Test sending a single email"""
        payload = {
            "recipient": self.test_email,
            "subject": "Test Email",
            "context": {
                "name": "Test User",
                "offer": "Test Offer",
                "custom_message": "This is a test message"
            }
        }
        
        response = requests.post(f"{self.api_url}/send-email", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"✅ Send single email test passed: {data['message']}")
        
    def test_send_bulk_email(self):
        """Test sending bulk emails with multiple subjects"""
        payload = {
            "recipients": [self.test_email, "test2@example.com"],
            "subjects": ["Test Bulk Email 1", "Test Bulk Email 2"],  # Multiple subjects, one per recipient
            "contexts": [
                {
                    "name": "Test User 1",
                    "offer": "Test Offer 1",
                    "custom_message": "This is test message 1"
                },
                {
                    "name": "Test User 2",
                    "offer": "Test Offer 2",
                    "custom_message": "This is test message 2"
                }
            ]
        }
        
        response = requests.post(f"{self.api_url}/send-bulk-email", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"✅ Send bulk email test passed: {data['message']}")
        
    def test_schedule_email(self):
        """Test scheduling an email"""
        # Schedule for 5 minutes in the future
        schedule_time = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        payload = {
            "recipient": self.test_email,
            "subject": "Test Scheduled Email",
            "context": {
                "name": "Test User",
                "offer": "Test Offer",
                "custom_message": "This is a scheduled test message"
            },
            "schedule_time": schedule_time
        }
        
        response = requests.post(f"{self.api_url}/schedule-email", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue("job_id" in data)
        print(f"✅ Schedule email test passed: {data['message']}")
        
    def test_get_scheduled_emails(self):
        """Test retrieving scheduled emails"""
        response = requests.get(f"{self.api_url}/scheduled-emails")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue("scheduled_emails" in data)
        print(f"✅ Get scheduled emails test passed: {len(data['scheduled_emails'])} scheduled emails found")
        
    def test_get_email_logs(self):
        """Test retrieving email logs"""
        response = requests.get(f"{self.api_url}/email-logs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue("logs" in data)
        print(f"✅ Get email logs test passed: {len(data['logs'])} logs found")
        
    def test_invalid_email_format(self):
        """Test sending email with invalid email format"""
        payload = {
            "recipient": "invalid-email",
            "subject": "Test Email",
            "context": {
                "name": "Test User",
                "offer": "Test Offer",
                "custom_message": "This is a test message"
            }
        }
        
        response = requests.post(f"{self.api_url}/send-email", json=payload)
        self.assertNotEqual(response.status_code, 200)
        print("✅ Invalid email format test passed")
        
    def test_past_schedule_time(self):
        """Test scheduling an email with past time"""
        # Schedule for 5 minutes in the past
        schedule_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        payload = {
            "recipient": self.test_email,
            "subject": "Test Past Scheduled Email",
            "context": {
                "name": "Test User",
                "offer": "Test Offer",
                "custom_message": "This is a scheduled test message"
            },
            "schedule_time": schedule_time
        }
        
        response = requests.post(f"{self.api_url}/schedule-email", json=payload)
        self.assertNotEqual(response.status_code, 200)
        print("✅ Past schedule time test passed")
        
    def test_missing_required_fields(self):
        """Test sending email with missing required fields"""
        # Missing recipient
        payload = {
            "subject": "Test Email",
            "context": {
                "name": "Test User",
                "offer": "Test Offer",
                "custom_message": "This is a test message"
            }
        }
        
        response = requests.post(f"{self.api_url}/send-email", json=payload)
        self.assertNotEqual(response.status_code, 200)
        print("✅ Missing required fields test passed")
        
    def test_custom_template(self):
        """Test sending email with custom template"""
        custom_template = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Custom Template Test</h1>
            <p>Hello {{ context.name }},</p>
            <p>{{ context.offer }}</p>
            <p>{{ context.custom_message }}</p>
        </body>
        </html>
        """
        
        payload = {
            "recipient": self.test_email,
            "subject": "Test Custom Template",
            "context": {
                "name": "Test User",
                "offer": "Test Offer",
                "custom_message": "This is a test message"
            },
            "template": custom_template
        }
        
        response = requests.post(f"{self.api_url}/send-email", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"✅ Custom template test passed: {data['message']}")

    def test_comma_separated_subjects(self):
        """Test sending bulk email with comma-separated subjects"""
        payload = {
            "recipients": "test1@example.com, test2@example.com",
            "subjects": "Subject 1, Subject 2",
            "contexts": [
                {
                    "name": "Test User 1",
                    "offer": "Test Offer 1",
                    "custom_message": "This is test message 1"
                },
                {
                    "name": "Test User 2",
                    "offer": "Test Offer 2",
                    "custom_message": "This is test message 2"
                }
            ]
        }
        
        response = requests.post(f"{self.api_url}/send-bulk-email", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"✅ Comma-separated subjects test passed: {data['message']}")

    def test_multiline_subjects(self):
        """Test sending bulk email with subjects on multiple lines"""
        payload = {
            "recipients": """test1@example.com
test2@example.com""",
            "subjects": """Subject for user 1
Subject for user 2""",
            "contexts": [
                {
                    "name": "Test User 1",
                    "offer": "Test Offer 1",
                    "custom_message": "This is test message 1"
                },
                {
                    "name": "Test User 2",
                    "offer": "Test Offer 2",
                    "custom_message": "This is test message 2"
                }
            ]
        }
        
        response = requests.post(f"{self.api_url}/send-bulk-email", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"✅ Multiline subjects test passed: {data['message']}")

def run_tests():
    """Run all tests and print summary"""
    print("🚀 Starting API tests for Automatic Email Sender")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests to suite
    suite.addTest(EmailSenderAPITest("test_health_endpoint"))
    suite.addTest(EmailSenderAPITest("test_send_single_email"))
    suite.addTest(EmailSenderAPITest("test_send_bulk_email"))
    suite.addTest(EmailSenderAPITest("test_comma_separated_subjects"))
    suite.addTest(EmailSenderAPITest("test_multiline_subjects"))
    suite.addTest(EmailSenderAPITest("test_schedule_email"))
    suite.addTest(EmailSenderAPITest("test_get_scheduled_emails"))
    suite.addTest(EmailSenderAPITest("test_get_email_logs"))
    suite.addTest(EmailSenderAPITest("test_invalid_email_format"))
    suite.addTest(EmailSenderAPITest("test_past_schedule_time"))
    suite.addTest(EmailSenderAPITest("test_missing_required_fields"))
    suite.addTest(EmailSenderAPITest("test_custom_template"))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if not result.wasSuccessful():
        print("\nFailed tests:")
        for failure in result.failures:
            print(f"- {failure[0]}")
        for error in result.errors:
            print(f"- {error[0]}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()