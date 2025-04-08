# app/utils/validation.py
import re
import bleach
from datetime import datetime
from flask import request, jsonify

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_date(date_str, format='%Y-%m-%d'):
    """Validate date format"""
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def sanitize_input(text):
    """Sanitize input text to prevent XSS attacks"""
    return bleach.clean(text)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

class RequestValidator:
    """Utility class for validating request data"""
    
    def __init__(self, request_data):
        self.data = request_data
        self.errors = {}
        
    def validate_required(self, field, message=None):
        """Validate required field"""
        if field not in self.data or not self.data[field]:
            self.errors[field] = message or f"{field} is required"
        return self
        
    def validate_email(self, field, message=None):
        """Validate email format"""
        if field in self.data and self.data[field]:
            if not validate_email(self.data[field]):
                self.errors[field] = message or "Invalid email format"
        return self
        
    def validate_length(self, field, min_length=None, max_length=None, message=None):
        """Validate field length"""
        if field in self.data and self.data[field]:
            length = len(str(self.data[field]))
            
            if min_length and length < min_length:
                self.errors[field] = message or f"{field} must be at least {min_length} characters"
            
            if max_length and length > max_length:
                self.errors[field] = message or f"{field} must be at most {max_length} characters"
        
        return self
        
    def validate_numeric(self, field, min_value=None, max_value=None, message=None):
        """Validate numeric field"""
        if field in self.data and self.data[field]:
            try:
                value = float(self.data[field])
                
                if min_value is not None and value < min_value:
                    self.errors[field] = message or f"{field} must be at least {min_value}"
                
                if max_value is not None and value > max_value:
                    self.errors[field] = message or f"{field} must be at most {max_value}"
            
            except ValueError:
                self.errors[field] = message or f"{field} must be a number"
        
        return self
        
    def validate_date(self, field, format='%Y-%m-%d', message=None):
        """Validate date field"""
        if field in self.data and self.data[field]:
            if not validate_date(self.data[field], format):
                self.errors[field] = message or f"{field} must be a valid date in format {format}"
        
        return self
        
    def validate_in_list(self, field, valid_values, message=None):
        """Validate field value is in a list of valid values"""
        if field in self.data and self.data[field]:
            if self.data[field] not in valid_values:
                self.errors[field] = message or f"{field} must be one of: {', '.join(valid_values)}"
        
        return self
        
    def is_valid(self):
        """Check if validation passed"""
        return len(self.errors) == 0
        
    def get_errors(self):
        """Get validation errors"""
        return self.errors 