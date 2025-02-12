import re
from typing import Tuple, List
from pydantic import BaseModel

class PasswordValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("Password validation failed")

class PasswordStrength(BaseModel):
    score: int
    suggestions: List[str]
    is_valid: bool

def validate_password(password: str) -> PasswordStrength:
    errors = []
    suggestions = []
    score = 0

    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    else:
        score += 1

    if len(password) >= 12:
        score += 1

    # Uppercase check
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    else:
        score += 1

    # Lowercase check
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    else:
        score += 1

    # Number check
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    else:
        score += 1

    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    else:
        score += 1

    # Common password patterns
    common_patterns = [
        r'123456',
        r'password',
        r'qwerty',
        r'admin',
        r'letmein',
        r'welcome'
    ]
    
    if any(re.search(pattern, password.lower()) for pattern in common_patterns):
        errors.append("Password contains common patterns that are easily guessed")
        score = max(0, score - 2)

    # Repeated characters
    if re.search(r'(.)\1{2,}', password):
        suggestions.append("Avoid using repeated characters")
        score = max(0, score - 1)

    # Sequential characters
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mnop|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', 
                 password.lower()):
        suggestions.append("Avoid using sequential characters")
        score = max(0, score - 1)

    # Keyboard patterns
    keyboard_patterns = [
        r'qwerty',
        r'asdfgh',
        r'zxcvbn'
    ]
    
    if any(re.search(pattern, password.lower()) for pattern in keyboard_patterns):
        suggestions.append("Avoid using keyboard patterns")
        score = max(0, score - 1)

    # Additional suggestions for stronger passwords
    if score < 4:
        suggestions.append("Consider using a longer password")
        suggestions.append("Mix uppercase and lowercase letters")
        suggestions.append("Add numbers and special characters")

    return PasswordStrength(
        score=score,
        suggestions=suggestions,
        is_valid=len(errors) == 0
    )
