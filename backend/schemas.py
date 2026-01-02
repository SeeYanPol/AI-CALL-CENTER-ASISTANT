"""
Request validation schemas using Marshmallow
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from email_validator import validate_email as email_validate, EmailNotValidError
import bleach


class UserRegistrationSchema(Schema):
    """Schema for user registration"""
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True
    )
    full_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=255)
    )
    role = fields.Str(
        validate=validate.OneOf(['admin', 'trainer', 'trainee']),
        missing='trainee'
    )
    
    @validates('email')
    def validate_email(self, value):
        """Validate email format"""
        try:
            email_validate(value)
        except EmailNotValidError as e:
            raise ValidationError(str(e))
    
    @validates('password')
    def validate_password(self, value):
        """Validate password strength"""
        if not any(char.isdigit() for char in value):
            raise ValidationError('Password must contain at least one digit')
        if not any(char.isupper() for char in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in value):
            raise ValidationError('Password must contain at least one lowercase letter')
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize input data"""
        if 'full_name' in data:
            data['full_name'] = bleach.clean(data['full_name'])
        return data


class UserLoginSchema(Schema):
    """Schema for user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UserUpdateSchema(Schema):
    """Schema for user profile updates"""
    full_name = fields.Str(validate=validate.Length(min=2, max=255))
    email = fields.Email()
    
    @validates('email')
    def validate_email(self, value):
        """Validate email format"""
        try:
            email_validate(value)
        except EmailNotValidError as e:
            raise ValidationError(str(e))
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize input data"""
        if 'full_name' in data:
            data['full_name'] = bleach.clean(data['full_name'])
        return data


class PasswordChangeSchema(Schema):
    """Schema for password change"""
    old_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True
    )
    
    @validates('new_password')
    def validate_password(self, value):
        """Validate password strength"""
        if not any(char.isdigit() for char in value):
            raise ValidationError('Password must contain at least one digit')
        if not any(char.isupper() for char in value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in value):
            raise ValidationError('Password must contain at least one lowercase letter')


class SessionStartSchema(Schema):
    """Schema for starting a call session"""
    caller_info = fields.Dict(missing=dict)


class ChatMessageSchema(Schema):
    """Schema for chat messages"""
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=1000)
    )
    session_id = fields.Str()
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize message content"""
        if 'message' in data:
            # Allow basic text, strip HTML
            data['message'] = bleach.clean(
                data['message'],
                tags=[],
                strip=True
            ).strip()
        return data


class TTSRequestSchema(Schema):
    """Schema for text-to-speech requests"""
    text = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500)
    )
    lang = fields.Str(
        validate=validate.OneOf(['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh-CN']),
        missing='en'
    )
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize text content"""
        if 'text' in data:
            data['text'] = bleach.clean(
                data['text'],
                tags=[],
                strip=True
            ).strip()
        return data


class PaginationSchema(Schema):
    """Schema for pagination parameters"""
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), missing=20)


class SessionQuerySchema(PaginationSchema):
    """Schema for querying call sessions"""
    status = fields.Str(validate=validate.OneOf(['active', 'ended', 'abandoned']))
    start_date = fields.DateTime()
    end_date = fields.DateTime()
