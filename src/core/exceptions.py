class JuizMCPException(Exception):
    """Base exception for all Juiz MCP errors"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class DatabaseException(JuizMCPException):
    """Database related exceptions"""
    pass

class ValidationException(JuizMCPException):
    """Input validation exceptions"""
    pass

class NotFoundError(JuizMCPException):
    """Resource not found exceptions"""
    pass

class PermissionError(JuizMCPException):
    """Permission/authorization exceptions"""
    pass