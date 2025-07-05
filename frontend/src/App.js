import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const App = () => {
  const [activeTab, setActiveTab] = useState('send');
  const [formData, setFormData] = useState({
    recipients: '',
    subject: '',
    subjects: '', // Multiple subjects (one per line or comma-separated)
    name: '',
    offer: '',
    customMessage: '',
    customMessages: '', // Multiple custom messages (para by para)
    template: '',
    scheduleTime: '',
    isBulk: false,
    isScheduled: false,
    personalizedEmails: [''] // Array to store personalized email bodies
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [scheduledEmails, setScheduledEmails] = useState([]);
  const [emailLogs, setEmailLogs] = useState([]);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    if (activeTab === 'scheduled') {
      fetchScheduledEmails();
    } else if (activeTab === 'logs') {
      fetchEmailLogs();
    }
  }, [activeTab]);

  const fetchScheduledEmails = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/scheduled-emails`);
      setScheduledEmails(response.data.scheduled_emails || []);
    } catch (error) {
      console.error('Error fetching scheduled emails:', error);
    }
  };

  const fetchEmailLogs = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/email-logs`);
      setEmailLogs(response.data.logs || []);
    } catch (error) {
      console.error('Error fetching email logs:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handlePersonalizedEmailChange = (index, value) => {
    setFormData(prev => ({
      ...prev,
      personalizedEmails: prev.personalizedEmails.map((email, i) => 
        i === index ? value : email
      )
    }));
  };

  const addPersonalizedEmail = () => {
    setFormData(prev => ({
      ...prev,
      personalizedEmails: [...prev.personalizedEmails, '']
    }));
  };

  const removePersonalizedEmail = (index) => {
    setFormData(prev => ({
      ...prev,
      personalizedEmails: prev.personalizedEmails.filter((_, i) => i !== index)
    }));
  };

  const syncPersonalizedEmails = () => {
    const recipients = parseRecipients(formData.recipients);
    const currentEmails = formData.personalizedEmails;
    
    // Adjust the array to match the number of recipients
    const adjustedEmails = recipients.map((_, index) => 
      currentEmails[index] || ''
    );
    
    setFormData(prev => ({
      ...prev,
      personalizedEmails: adjustedEmails
    }));
  };

  const showMessage = (msg, type) => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const validateForm = () => {
    if (!formData.recipients.trim()) {
      showMessage('Please enter at least one recipient email address', 'error');
      return false;
    }
    if (!formData.subjects.trim() && !formData.subject.trim()) {
      showMessage('Please enter at least one email subject', 'error');
      return false;
    }
    if (formData.isScheduled && !formData.scheduleTime) {
      showMessage('Please select a schedule time', 'error');
      return false;
    }
    return true;
  };

  const parseRecipients = (recipientsString) => {
    return recipientsString
      .split(/[,;\n]/)
      .map(email => email.trim())
      .filter(email => email && email.includes('@'));
  };

  const parseSubjects = (subjectsString) => {
    return subjectsString
      .split(/[,;\n]/)
      .map(subject => subject.trim())
      .filter(subject => subject);
  };

  const parseCustomMessages = (messagesString) => {
    return messagesString
      .split(/\n\n+/) // Split by double newlines (paragraph breaks)
      .map(message => message.trim())
      .filter(message => message);
  };

  const handleSendEmail = async () => {
    if (!validateForm()) return;

    setLoading(true);
    
    try {
      const recipients = parseRecipients(formData.recipients);
      const subjects = parseSubjects(formData.subjects);
      const customMessages = parseCustomMessages(formData.customMessages);
      
      if (recipients.length === 0) {
        showMessage('Please enter valid email addresses', 'error');
        setLoading(false);
        return;
      }

      if (subjects.length === 0) {
        showMessage('Please enter at least one subject', 'error');
        setLoading(false);
        return;
      }

      let response;
      
      if (formData.isBulk && formData.personalizedEmails.some(email => email.trim())) {
        // Send personalized emails with different content for each recipient
        const results = [];
        
        for (let i = 0; i < recipients.length; i++) {
          const emailContent = formData.personalizedEmails[i] || formData.personalizedEmails[0] || '';
          const emailSubject = subjects[i] || subjects[subjects.length - 1] || subjects[0];
          
          if (!emailContent.trim()) {
            showMessage(`Please provide email content for recipient ${i + 1}`, 'error');
            setLoading(false);
            return;
          }
          
          const endpoint = formData.isScheduled ? '/api/schedule-personalized-email' : '/api/send-personalized-email';
          
          const payload = {
            recipient: recipients[i],
            subject: emailSubject,
            email_body: emailContent,
            ...(formData.isScheduled && { schedule_time: formData.scheduleTime })
          };

          try {
            const res = await axios.post(`${backendUrl}${endpoint}`, payload);
            results.push({ recipient: recipients[i], success: true, message: res.data.message });
          } catch (error) {
            results.push({ recipient: recipients[i], success: false, message: error.response?.data?.detail || error.message });
          }
        }
        
        const successful = results.filter(r => r.success).length;
        showMessage(`Personalized emails: ${successful}/${recipients.length} sent successfully`, 'success');
        
      } else if (formData.isBulk) {
        // Enhanced bulk email sending with multiple subjects and custom messages
        const results = [];
        
        for (let i = 0; i < recipients.length; i++) {
          const emailSubject = subjects[i] || subjects[subjects.length - 1] || subjects[0];
          const customMessage = customMessages[i] || customMessages[customMessages.length - 1] || formData.customMessage || '';
          
          const context = {
            name: formData.name || 'Valued Customer',
            offer: formData.offer || 'Special Offer',
            custom_message: customMessage
          };
          
          const endpoint = formData.isScheduled ? '/api/schedule-email' : '/api/send-email';
          
          const payload = {
            recipient: recipients[i],
            subject: emailSubject,
            context: context,
            template: formData.template || '',
            ...(formData.isScheduled && { schedule_time: formData.scheduleTime })
          };

          try {
            const res = await axios.post(`${backendUrl}${endpoint}`, payload);
            results.push({ recipient: recipients[i], success: true, message: res.data.message });
          } catch (error) {
            results.push({ recipient: recipients[i], success: false, message: error.response?.data?.detail || error.message });
          }
        }
        
        const successful = results.filter(r => r.success).length;
        showMessage(`Enhanced bulk emails: ${successful}/${recipients.length} sent successfully`, 'success');
        
      } else {
        // Single email sending
        const emailSubject = subjects[0] || formData.subject;
        const customMessage = customMessages[0] || formData.customMessage || '';
        
        const endpoint = formData.isScheduled ? '/api/schedule-email' : '/api/send-email';
        
        const payload = {
          recipient: recipients[0],
          subject: emailSubject,
          context: {
            name: formData.name || 'Valued Customer',
            offer: formData.offer || 'Special Offer',
            custom_message: customMessage
          },
          template: formData.template || '',
          ...(formData.isScheduled && { schedule_time: formData.scheduleTime })
        };

        response = await axios.post(`${backendUrl}${endpoint}`, payload);
        showMessage(response.data.message || 'Email sent successfully!', 'success');
      }
      
      // Reset form
      setFormData({
        recipients: '',
        subject: '',
        subjects: '',
        name: '',
        offer: '',
        customMessage: '',
        customMessages: '',
        template: '',
        scheduleTime: '',
        isBulk: false,
        isScheduled: false,
        personalizedEmails: ['']
      });

    } catch (error) {
      console.error('Error sending email:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to send email';
      showMessage(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="app">
      <div className="header">
        <h1>🚀 Automatic Email Sender</h1>
        <p>Gmail SMTP • Bulk Sending • Scheduling • Personalization</p>
      </div>

      <div className="tabs">
        <button 
          className={activeTab === 'send' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('send')}
        >
          📧 Send Emails
        </button>
        <button 
          className={activeTab === 'scheduled' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('scheduled')}
        >
          ⏰ Scheduled
        </button>
        <button 
          className={activeTab === 'logs' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('logs')}
        >
          📊 Logs
        </button>
      </div>

      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}

      {activeTab === 'send' && (
        <div className="tab-content">
          <div className="form-section">
            <h3>📬 Email Configuration</h3>
            
            <div className="form-group">
              <label>Recipients (one per line or comma-separated):</label>
              <textarea
                name="recipients"
                value={formData.recipients}
                onChange={handleInputChange}
                placeholder="user1@example.com&#10;user2@example.com&#10;user3@example.com"
                rows="4"
                required
              />
            </div>

            <div className="form-group">
              <label>Subjects (one per line or comma-separated):</label>
              <textarea
                name="subjects"
                value={formData.subjects}
                onChange={handleInputChange}
                placeholder="Subject for recipient 1&#10;Subject for recipient 2&#10;Subject for recipient 3"
                rows="4"
                required
              />
              <p className="helper-text">Enter multiple subjects - one for each recipient. If fewer subjects than recipients, the last subject will be reused.</p>
            </div>

            <div className="form-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="isBulk"
                  checked={formData.isBulk}
                  onChange={handleInputChange}
                />
                <span>📦 Bulk email mode</span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="isScheduled"
                  checked={formData.isScheduled}
                  onChange={handleInputChange}
                />
                <span>⏰ Schedule sending</span>
              </label>
            </div>

            {formData.isBulk && (
              <div className="form-group">
                <button 
                  type="button" 
                  className="sync-button"
                  onClick={syncPersonalizedEmails}
                >
                  🔄 Sync Email Templates with Recipients
                </button>
                <p className="helper-text">Click to create email templates for each recipient based on your recipients list</p>
              </div>
            )}

            {formData.isScheduled && (
              <div className="form-group">
                <label>Schedule Time:</label>
                <input
                  type="datetime-local"
                  name="scheduleTime"
                  value={formData.scheduleTime}
                  onChange={handleInputChange}
                  min={new Date().toISOString().slice(0, 16)}
                  required
                />
              </div>
            )}
          </div>

          {/* Personalized Email Bodies Section */}
          {formData.isBulk && formData.personalizedEmails.length > 0 && (
            <div className="form-section">
              <h3>✉️ Personalized Email Bodies</h3>
              <p className="helper-text">Create unique email content for each recipient. Each email will be sent to the corresponding recipient in your list.</p>
              
              {formData.personalizedEmails.map((emailBody, index) => (
                <div key={index} className="personalized-email-item">
                  <div className="personalized-email-header">
                    <label>Email {index + 1} - Recipient: {parseRecipients(formData.recipients)[index] || 'Not specified'}</label>
                    {formData.personalizedEmails.length > 1 && (
                      <button 
                        type="button" 
                        className="remove-button"
                        onClick={() => removePersonalizedEmail(index)}
                      >
                        ❌ Remove
                      </button>
                    )}
                  </div>
                  <textarea
                    value={emailBody}
                    onChange={(e) => handlePersonalizedEmailChange(index, e.target.value)}
                    placeholder={`Enter personalized email content for recipient ${index + 1}...

Example:
Subject: Your subject here

Hi [Company Name] Team,

Your personalized message here...

Best regards,
Your Name
Your Title
📧 your.email@company.com
📞 +1234567890`}
                    rows="8"
                    className="personalized-email-textarea"
                  />
                </div>
              ))}
              
              <button 
                type="button" 
                className="add-button"
                onClick={addPersonalizedEmail}
              >
                ➕ Add Another Personalized Email
              </button>
            </div>
          )}

          {/* Enhanced Personalization Section */}
          <div className="form-section">
            <h3>🎨 Email Content</h3>
            
            <div className="form-group">
              <label>Custom Messages (separate each message with double line breaks):</label>
              <textarea
                name="customMessages"
                value={formData.customMessages}
                onChange={handleInputChange}
                placeholder="Hi Team,

We hope this message finds you well. We're excited to share this opportunity with you.

Want to explore more about our services? Feel free to reach out.

Best regards,
Your Name
your.email@company.com
+1234567890

---

Hi [Company Name],

Thank you for your interest in our services. We'd love to discuss how we can help you achieve your goals.

Looking forward to connecting with you soon.

Best regards,
Your Name
your.email@company.com
+1234567890"
                rows="12"
                className="personalized-messages-textarea"
              />
              <p className="helper-text">📧 <strong>Note:</strong> Emails will be sent as simple plain text (like the professional emails you receive daily). Separate each message with double line breaks for different recipients.</p>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Default Recipient Name (fallback):</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Team / Company Name"
                />
              </div>

              <div className="form-group">
                <label>Default Offer/Content (fallback):</label>
                <input
                  type="text"
                  name="offer"
                  value={formData.offer}
                  onChange={handleInputChange}
                  placeholder="Your offer or main content"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Default Custom Message (fallback):</label>
              <textarea
                name="customMessage"
                value={formData.customMessage}
                onChange={handleInputChange}
                placeholder="Hi there,

Thank you for your interest. We'd love to connect with you.

Best regards,
Your Name"
                rows="4"
              />
            </div>
          </div>

          {/* Email Template Section (for template-based emails) */}
          {(!formData.isBulk || !formData.personalizedEmails.some(email => email.trim())) && (
            <div className="form-section">
              <h3>📝 Email Template (Optional)</h3>
              <p className="helper-text">Leave blank to use the default template. Use template variables like {"{context.name}"} and {"{context.offer}"}</p>
              
              <div className="form-group">
                <textarea
                  name="template"
                  value={formData.template}
                  onChange={handleInputChange}
                  placeholder="Enter custom HTML email template..."
                  rows="6"
                  className="template-input"
                />
              </div>
            </div>
          )}

          <div className="form-actions">
            <button 
              className="send-button"
              onClick={handleSendEmail}
              disabled={loading}
            >
              {loading ? (
                <span>⏳ Processing...</span>
              ) : formData.isScheduled ? (
                <span>⏰ Schedule Email{formData.isBulk ? 's' : ''}</span>
              ) : (
                <span>🚀 Send Email{formData.isBulk ? 's' : ''} Now</span>
              )}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'scheduled' && (
        <div className="tab-content">
          <h3>⏰ Scheduled Emails</h3>
          {scheduledEmails.length === 0 ? (
            <p className="empty-state">No scheduled emails found.</p>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Recipient</th>
                    <th>Subject</th>
                    <th>Scheduled Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {scheduledEmails.map((email, index) => (
                    <tr key={index}>
                      <td>{email.recipient || email.recipients?.join(', ')}</td>
                      <td>{email.subject}</td>
                      <td>{formatDateTime(email.schedule_time)}</td>
                      <td><span className="status-badge scheduled">{email.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="tab-content">
          <h3>📊 Email Logs</h3>
          {emailLogs.length === 0 ? (
            <p className="empty-state">No email logs found.</p>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Recipient</th>
                    <th>Subject</th>
                    <th>Sent Time</th>
                    <th>Status</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {emailLogs.map((log, index) => (
                    <tr key={index}>
                      <td>{log.recipient || log.recipients?.join(', ')}</td>
                      <td>{log.subject}</td>
                      <td>{formatDateTime(log.sent_at)}</td>
                      <td>
                        <span className={`status-badge ${log.success ? 'success' : 'error'}`}>
                          {log.success ? 'Sent' : 'Failed'}
                        </span>
                      </td>
                      <td>{log.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="footer">
        <p>🔧 Built with FastAPI + React + Gmail SMTP</p>
        <p>📧 Sending from: hackfinity.innovation@gmail.com</p>
      </div>
    </div>
  );
};

export default App;