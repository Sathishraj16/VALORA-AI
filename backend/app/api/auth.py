"""
VALORA Authentication API Router
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid

from ..core.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# In-memory user store (replace with database in production)
users_db: dict = {}


class UserCreate(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    organization: Optional[str] = None


class UserResponse(BaseModel):
    """User response"""
    id: str
    email: str
    name: str
    organization: Optional[str]
    created_at: str
    is_active: bool


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class User:
    """User model"""
    def __init__(self, id: str, email: str, password_hash: str, name: str, 
                 organization: Optional[str] = None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.organization = organization
        self.created_at = datetime.utcnow()
        self.is_active = True
        self.refresh_tokens: set = set()


def hash_password(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create an access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user"""
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user = users_db[user_id]
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is disabled"
        )
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserCreate):
    """Register a new user"""
    # Check if email already exists
    for user in users_db.values():
        if user.email == request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
        organization=request.organization
    )
    users_db[user_id] = user
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization=user.organization,
        created_at=user.created_at.isoformat(),
        is_active=user.is_active
    )


@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get tokens"""
    # Find user by email
    user = None
    for u in users_db.values():
        if u.email == form_data.username:
            user = u
            break
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is disabled"
        )
    
    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Store refresh token
    user.refresh_tokens.add(refresh_token)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token"""
    payload = decode_token(request.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    user = users_db[user_id]
    
    # Validate refresh token is still valid
    if request.refresh_token not in user.refresh_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Rotate tokens
    user.refresh_tokens.discard(request.refresh_token)
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    user.refresh_tokens.add(new_refresh_token)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """Logout user"""
    # Clear all refresh tokens
    current_user.refresh_tokens.clear()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        organization=current_user.organization,
        created_at=current_user.created_at.isoformat(),
        is_active=current_user.is_active
    )


@router.put("/me", response_model=UserResponse)
async def update_me(
    name: Optional[str] = None,
    organization: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    if name:
        current_user.name = name
    if organization:
        current_user.organization = organization
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        organization=current_user.organization,
        created_at=current_user.created_at.isoformat(),
        is_active=current_user.is_active
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Change password"""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.password_hash = hash_password(request.new_password)
    # Invalidate all refresh tokens
    current_user.refresh_tokens.clear()
    
    return {"message": "Password changed successfully"}


@router.delete("/me")
async def delete_account(current_user: User = Depends(get_current_user)):
    """Delete current user account"""
    del users_db[current_user.id]
    return {"message": "Account deleted successfully"}


# API Key management for programmatic access
api_keys_db: dict = {}


class APIKeyCreate(BaseModel):
    """API key creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: int = Field(default=365, ge=1, le=730)


class APIKeyResponse(BaseModel):
    """API key response"""
    id: str
    name: str
    key: str  # Only shown once on creation
    created_at: str
    expires_at: str


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreate,
    current_user: User = Depends(get_current_user)
):
    """Create an API key"""
    import secrets
    
    key_id = str(uuid.uuid4())
    api_key = f"valora_{secrets.token_urlsafe(32)}"
    
    expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
    
    api_keys_db[key_id] = {
        "id": key_id,
        "name": request.name,
        "key_hash": hash_password(api_key),
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    }
    
    return APIKeyResponse(
        id=key_id,
        name=request.name,
        key=api_key,  # Only returned once
        created_at=datetime.utcnow().isoformat(),
        expires_at=expires_at.isoformat()
    )


@router.get("/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """List user's API keys"""
    user_keys = [
        {
            "id": k["id"],
            "name": k["name"],
            "created_at": k["created_at"].isoformat(),
            "expires_at": k["expires_at"].isoformat()
        }
        for k in api_keys_db.values()
        if k["user_id"] == current_user.id
    ]
    return {"api_keys": user_keys}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an API key"""
    if key_id not in api_keys_db:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if api_keys_db[key_id]["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    del api_keys_db[key_id]
    return {"message": "API key deleted"}
