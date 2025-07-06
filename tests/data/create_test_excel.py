import pandas as pd

# Create a simple Excel file with test data
data = {
    'email': ['test1@example.com', 'test2@example.com', 'test3@example.com', 'test4@example.com'],
    'subject': ['Test Subject 1', 'Test Subject 2', 'Test Subject 3', 'Test Subject 4'],
    'body': [
        'Hello Test User 1,\n\nThis is a test email body 1.\n\nBest regards,\nTest Sender',
        'Hello Test User 2,\n\nThis is a test email body 2.\n\nBest regards,\nTest Sender',
        'Hello Test User 3,\n\nThis is a test email body 3.\n\nBest regards,\nTest Sender',
        'Hello Test User 4,\n\nThis is a test email body 4.\n\nBest regards,\nTest Sender'
    ],
    'name': ['Test User 1', 'Test User 2', 'Test User 3', 'Test User 4']
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel file
df.to_excel('/app/tests/data/test_emails.xlsx', index=False)

print("Test Excel file created at /app/tests/data/test_emails.xlsx")

# Create a file with missing columns for error testing
data_missing = {
    'email': ['test1@example.com', 'test2@example.com'],
    'name': ['Test User 1', 'Test User 2']
}

# Create DataFrame
df_missing = pd.DataFrame(data_missing)

# Save to Excel file
df_missing.to_excel('/app/tests/data/test_emails_missing_columns.xlsx', index=False)

print("Test Excel file with missing columns created at /app/tests/data/test_emails_missing_columns.xlsx")

# Create an empty Excel file for error testing
df_empty = pd.DataFrame()
df_empty.to_excel('/app/tests/data/test_emails_empty.xlsx', index=False)

print("Empty test Excel file created at /app/tests/data/test_emails_empty.xlsx")