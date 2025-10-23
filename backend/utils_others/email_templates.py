from typing import Dict, Any
from pathlib import Path
import os
from jinja2 import Environment, FileSystemLoader

class EmailTemplates:
    def __init__(self):
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
    def registration_confirmation(self, user_data: Dict[str, Any]) -> str:
        """Generate registration confirmation email"""
        template = self.env.get_template('registration_confirmation.html')
        return template.render(
            name=user_data['full_name'],
            role=user_data['role'],
            login_url='https://login.skreenit.com/login.html'
        )
        
    def recruiter_welcome(self, user_data: Dict[str, Any]) -> str:
        """Generate recruiter welcome email with company ID"""
        template = self.env.get_template('recruiter_welcome.html')
        return template.render(
            name=user_data['full_name'],
            email=user_data['email'],
            company_id=user_data['company_id'],
            login_url='https://login.skreenit.com/login.html'
        )
        
    def password_reset(self, user_data: Dict[str, Any]) -> str:
        """Generate password reset email"""
        template = self.env.get_template('password_reset.html')
        return template.render(
            name=user_data['full_name'],
            reset_url=user_data['reset_url']
        )
        
    def password_updated(self, user_data: Dict[str, Any]) -> str:
        """Generate password updated confirmation email"""
        template = self.env.get_template('password_updated.html')
        return template.render(
            name=user_data['full_name'],
            login_url='https://login.skreenit.com/login.html'
        )

# Create email templates directory and files
template_dir = Path('backend/utils_others/templates')
template_dir.mkdir(exist_ok=True)

# Registration confirmation template
registration_template = """
<!DOCTYPE html>
<html>
<body>
    <h2>Welcome to Skreenit!</h2>
    <p>Dear {{ name }},</p>
    <p>Thank you for registering with Skreenit as a {{ role }}.</p>
    <p>Please click the verification link in your email to confirm your address and set up your password.</p>
    <p>After verification, you can login here:</p>
    <p><a href="{{ login_url }}">{{ login_url }}</a></p>
    <p>Best regards,<br>The Skreenit Team</p>
</body>
</html>
"""

# Recruiter welcome template
recruiter_template = """
<!DOCTYPE html>
<html>
<body>
    <h2>Welcome to Skreenit!</h2>
    <p>Dear {{ name }},</p>
    <p>Your recruiter account has been created successfully.</p>
    <p><strong>Important Information:</strong></p>
    <ul>
        <li><strong>Login Email:</strong> {{ email }}</li>
        <li><strong>Company ID:</strong> {{ company_id }}</li>
    </ul>
    <p>You'll need your Company ID for future logins.</p>
    <p>Please click the verification link in your email to confirm your address and set up your password.</p>
    <p>After verification, you can login here:</p>
    <p><a href="{{ login_url }}">{{ login_url }}</a></p>
    <p>Best regards,<br>The Skreenit Team</p>
</body>
</html>
"""

# Password reset template
password_reset_template = """
<!DOCTYPE html>
<html>
<body>
    <h2>Reset Your Password</h2>
    <p>Dear {{ name }},</p>
    <p>We received a request to reset your password. Click the link below to create a new password:</p>
    <p><a href="{{ reset_url }}">Reset Password</a></p>
    <p>If you didn't request this change, please ignore this email.</p>
    <p>Best regards,<br>The Skreenit Team</p>
</body>
</html>
"""

# Password updated template
password_updated_template = """
<!DOCTYPE html>
<html>
<body>
    <h2>Password Updated Successfully</h2>
    <p>Dear {{ name }},</p>
    <p>Your password has been updated successfully.</p>
    <p>You can now login with your new password here:</p>
    <p><a href="{{ login_url }}">{{ login_url }}</a></p>
    <p>Best regards,<br>The Skreenit Team</p>
</body>
</html>
"""

# Save templates
templates = {
    'registration_confirmation.html': registration_template,
    'recruiter_welcome.html': recruiter_template,
    'password_reset.html': password_reset_template,
    'password_updated.html': password_updated_template
}

for filename, content in templates.items():
    with open(template_dir / filename, 'w') as f:
        f.write(content)