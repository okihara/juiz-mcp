from typing import Dict, Any, Optional
from src.core.exceptions import JuizMCPException

class ResponseFormatter:
    """Standardized response formatting"""
    
    @staticmethod
    def success(data: Any, message: str = None) -> Dict[str, Any]:
        """Format successful response"""
        response = {
            "success": True,
            "data": data
        }
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error(error: str, error_code: str = None, status_code: int = 400) -> Dict[str, Any]:
        """Format error response"""
        response = {
            "success": False,
            "error": error,
            "status_code": status_code
        }
        if error_code:
            response["error_code"] = error_code
        return response
    
    @staticmethod
    def from_exception(exception: Exception) -> Dict[str, Any]:
        """Format response from exception"""
        if isinstance(exception, JuizMCPException):
            return ResponseFormatter.error(
                error=exception.message,
                error_code=exception.error_code,
                status_code=400
            )
        else:
            return ResponseFormatter.error(
                error=str(exception),
                error_code="INTERNAL_ERROR",
                status_code=500
            )