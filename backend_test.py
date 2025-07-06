import requests
import unittest
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import io

class EmailSenderAPITest(unittest.TestCase):
    """Test suite for the Automatic Email Sender API"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Use the public endpoint from frontend/.env
        self.base_url = "https://0d9ea18d-b08b-4851-b1c4-c0d1d80e070d.preview.emergentagent.com"
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
        
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        response = requests.get(f"{self.api_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Automatic Email Sender API" in response.text)
        print("✅ Root endpoint test passed")
        
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

    def create_test_excel_file(self, filename="test_data.xlsx"):
        """Create a test Excel file for testing"""
        # Create a DataFrame with test data
        data = {
            "email": ["test@example.com", "test2@example.com", "invalid-email"],
            "subject": ["Test Subject 1", "Test Subject 2", "Test Subject 3"],
            "body": ["Test email body 1", "Test email body 2", "Test email body 3"],
            "name": ["Test User 1", "Test User 2", "Test User 3"]
        }
        df = pd.DataFrame(data)
        
        # Save to Excel file
        df.to_excel(filename, index=False)
        print(f"✅ Created test Excel file: {filename}")
        return filename
    
    def test_upload_valid_excel(self):
        """Test uploading a valid Excel file"""
        # Create test Excel file
        filename = self.create_test_excel_file()
        
        # Upload the file
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{self.api_url}/upload-excel", files=files)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue("columns" in data)
        self.assertTrue(len(data["columns"]) > 0)
        self.assertTrue("email" in data["columns"])
        self.assertTrue("subject" in data["columns"])
        self.assertTrue("body" in data["columns"])
        print(f"✅ Upload valid Excel test passed: {data['message']}")
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_upload_invalid_file(self):
        """Test uploading an invalid file format"""
        # Create a text file
        filename = "invalid_file.txt"
        with open(filename, 'w') as f:
            f.write("This is not an Excel file")
        
        # Upload the file
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            response = requests.post(f"{self.api_url}/upload-excel", files=files)
        
        # Verify response
        self.assertNotEqual(response.status_code, 200)
        print("✅ Upload invalid file test passed")
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_process_excel_valid_mapping(self):
        """Test processing Excel file with valid column mapping"""
        # Create test Excel file
        filename = self.create_test_excel_file()
        
        # Define column mapping
        mapping = {
            "email_column": "email",
            "subject_column": "subject",
            "body_column": "body",
            "name_column": "name"
        }
        
        # Upload and process the file
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(
                f"{self.api_url}/process-excel",
                files=files,
                data={"mapping": json.dumps(mapping)}
            )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue("emails" in data)
        self.assertTrue(len(data["emails"]) > 0)
        self.assertEqual(data["emails"][0]["email"], "test@example.com")
        self.assertEqual(data["emails"][0]["subject"], "Test Subject 1")
        print(f"✅ Process Excel with valid mapping test passed: {data['message']}")
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_process_excel_missing_columns(self):
        """Test processing Excel with missing required columns"""
        # Create a DataFrame with missing columns
        data = {
            "email": ["test@example.com", "test2@example.com"],
            # Missing subject column
            "body": ["Test email body 1", "Test email body 2"],
        }
        filename = "missing_columns.xlsx"
        pd.DataFrame(data).to_excel(filename, index=False)
        
        # Define column mapping with non-existent column
        mapping = {
            "email_column": "email",
            "subject_column": "subject",  # This column doesn't exist
            "body_column": "body"
        }
        
        # Upload and process the file
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(
                f"{self.api_url}/process-excel",
                files=files,
                data={"mapping": json.dumps(mapping)}
            )
        
        # Verify response
        self.assertNotEqual(response.status_code, 200)
        print("✅ Process Excel with missing columns test passed")
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_send_excel_emails(self):
        """Test sending emails from Excel data"""
        # Create email data
        emails = [
            {
                "email": "test@example.com",
                "subject": "Test Excel Email 1",
                "body": "This is a test email body 1",
                "name": "Test User 1"
            },
            {
                "email": "test2@example.com",
                "subject": "Test Excel Email 2",
                "body": "This is a test email body 2",
                "name": "Test User 2"
            }
        ]
        
        # Send emails
        payload = {
            "emails": emails
        }
        
        response = requests.post(f"{self.api_url}/send-excel-emails", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue("results" in data)
        self.assertEqual(len(data["results"]), 2)
        print(f"✅ Send Excel emails test passed: {data['message']}")
    
    def test_schedule_excel_emails(self):
        """Test scheduling emails from Excel data"""
        # Schedule for 5 minutes in the future
        schedule_time = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        # Create email data
        emails = [
            {
                "email": "test@example.com",
                "subject": "Test Scheduled Excel Email 1",
                "body": "This is a scheduled test email body 1",
                "name": "Test User 1"
            },
            {
                "email": "test2@example.com",
                "subject": "Test Scheduled Excel Email 2",
                "body": "This is a scheduled test email body 2",
                "name": "Test User 2"
            }
        ]
        
        # Schedule emails
        payload = {
            "emails": emails,
            "schedule_time": schedule_time
        }
        
        response = requests.post(f"{self.api_url}/send-excel-emails", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue("scheduled_jobs" in data)
        self.assertEqual(len(data["scheduled_jobs"]), 2)
        print(f"✅ Schedule Excel emails test passed: {data['message']}")
    
    def test_send_excel_emails_empty_list(self):
        """Test sending emails with empty email list"""
        # Send empty email list
        payload = {
            "emails": []
        }
        
        response = requests.post(f"{self.api_url}/send-excel-emails", json=payload)
        self.assertNotEqual(response.status_code, 200)
        print("✅ Send Excel emails with empty list test passed")

def test_root_endpoint(self):
        """Test the root API endpoint"""
        response = requests.get(f"{self.api_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Automatic Email Sender API" in response.text)
        print("✅ Root endpoint test passed")

def run_tests():
    """Run all tests and print summary"""
    print("🚀 Starting API tests for Automatic Email Sender")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests to suite - focusing on the core API endpoints
    suite.addTest(EmailSenderAPITest("test_health_endpoint"))
    suite.addTest(EmailSenderAPITest("test_root_endpoint"))
    suite.addTest(EmailSenderAPITest("test_get_scheduled_emails"))
    suite.addTest(EmailSenderAPITest("test_get_email_logs"))
    
    # Add Excel functionality tests
    suite.addTest(EmailSenderAPITest("test_upload_valid_excel"))
    suite.addTest(EmailSenderAPITest("test_upload_invalid_file"))
    suite.addTest(EmailSenderAPITest("test_process_excel_valid_mapping"))
    suite.addTest(EmailSenderAPITest("test_process_excel_missing_columns"))
    suite.addTest(EmailSenderAPITest("test_send_excel_emails"))
    suite.addTest(EmailSenderAPITest("test_schedule_excel_emails"))
    suite.addTest(EmailSenderAPITest("test_send_excel_emails_empty_list"))
    
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