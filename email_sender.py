"""
This module opens the default email client prepopulated with multiple email addresses,
a subject, a body, and attaches the roster PDF.
"""

import os

def open_email_client(email_addresses, subject, body, attachment_path):
    """
    Open the default email client with a new email draft.
    
    If Microsoft Outlook is installed, this function uses win32com to create a draft
    with the To, Subject, Body, and Attachment fields prepopulated.
    Otherwise, it falls back to the mailto URL scheme (attachments are not supported with mailto).
    
    :param email_addresses: List of recipient email addresses.
    :param subject: The subject of the email.
    :param body: The email body text.
    :param attachment_path: File path to the PDF to be attached.
    """
    try:
        # Try Outlook automation (Windows only)
        import win32com.client
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)  # 0: Mail item
        mail.To = ";".join(email_addresses)
        mail.Subject = subject
        mail.Body = body
        if os.path.exists(attachment_path):
            mail.Attachments.Add(os.path.abspath(attachment_path))
        # Open the email draft window for review
        mail.Display(False)
    except Exception as e:
        # Fallback using mailto scheme
        try:
            import webbrowser
            print("Outlook automation failed, using mailto fallback. Error:", e)
            mailto_link = "mailto:" + ",".join(email_addresses)
            # Encode subject and body for URL
            mailto_link += f"?subject={subject}&body={body}"
            webbrowser.open(mailto_link)
        except Exception as inner_e:
            print("Mailto fallback failed:", inner_e)

# For testing: Uncomment to test the email sender.
# if __name__ == '__main__':
#     test_emails = ["employee1@example.com", "employee2@example.com"]
#     open_email_client(test_emails,
#                       "Roster for 2025-05-01 to 2025-05-07",
#                       "Please find attached the finalized roster.",
#                       "final_roster.pdf")
