"""
Pydantic schemas for the Smriti API.

These schemas define the structure of request and response data for API endpoints.
They are used for validation, serialization, and documentation.
"""
from datetime import datetime, date
from typing import List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


# Authentication schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data for JWT validation."""
    user_id: Optional[str] = None
    email: Optional[str] = None


# User schemas
class UserBase(BaseModel):
    """Base user data."""
    email: EmailStr


class UserCreate(UserBase):
    """Data required to create a new user."""
    password: str


class UserAuthenticate(UserBase):
    """Data required to authenticate a user."""
    password: str


class UserInDB(UserBase):
    """User data as stored in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """User data returned in API responses."""
    pass


# User profile schemas
class UserProfileBase(BaseModel):
    """Base user profile data."""
    display_name: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[str] = None
    language: str = "en"


class UserProfileCreate(UserProfileBase):
    """Data required to create a user profile."""
    pass


class UserProfileUpdate(UserProfileBase):
    """Data that can be updated in a user profile."""
    pass


class UserProfileInDB(UserProfileBase):
    """User profile data as stored in the database."""
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(UserProfileInDB):
    """User profile data returned in API responses."""
    pass


# Session schemas
class SessionBase(BaseModel):
    """Base session data."""
    duration_seconds: Optional[int] = None
    raw_transcript: Optional[str] = None


class SessionCreate(SessionBase):
    """Data required to create a new session."""
    user_id: UUID


class SessionInDB(SessionBase):
    """Session data as stored in the database."""
    id: UUID
    user_id: UUID
    created_at: datetime
    is_processed: bool
    
    class Config:
        from_attributes = True


class Session(SessionInDB):
    """Session data returned in API responses."""
    pass


# Node schemas
class NodeBase(BaseModel):
    """Base node data."""
    text: str
    emotion: Optional[str] = None
    theme: Optional[str] = None
    cognition_type: Optional[str] = None


class NodeCreate(NodeBase):
    """Data required to create a new node."""
    user_id: UUID
    session_id: UUID


class NodeInDB(NodeBase):
    """Node data as stored in the database."""
    id: UUID
    user_id: UUID
    session_id: UUID
    created_at: datetime
    is_processed: bool
    
    class Config:
        from_attributes = True


class Node(NodeInDB):
    """Node data returned in API responses."""
    pass


# Edge schemas
class EdgeBase(BaseModel):
    """Base edge data."""
    edge_type: str
    match_strength: float = Field(ge=0.0, le=1.0)
    session_relation: str
    explanation: Optional[str] = None


class EdgeCreate(EdgeBase):
    """Data required to create a new edge."""
    from_node: UUID
    to_node: UUID
    user_id: UUID


class EdgeInDB(EdgeBase):
    """Edge data as stored in the database."""
    id: UUID
    from_node: UUID
    to_node: UUID
    user_id: UUID
    created_at: datetime
    is_processed: bool
    
    class Config:
        from_attributes = True


class Edge(EdgeInDB):
    """Edge data returned in API responses."""
    pass


# Reflection schemas
class ReflectionBase(BaseModel):
    """Base reflection data."""
    generated_text: str
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class ReflectionCreate(ReflectionBase):
    """Data required to create a new reflection."""
    user_id: UUID
    node_ids: List[UUID]
    edge_ids: Optional[List[UUID]] = None


class ReflectionInDB(ReflectionBase):
    """Reflection data as stored in the database."""
    id: UUID
    user_id: UUID
    node_ids: List[UUID]
    edge_ids: Optional[List[UUID]]
    generated_at: datetime
    is_reflected: bool
    is_viewed: bool
    feedback: Optional[int] = None
    
    class Config:
        from_attributes = True


class Reflection(ReflectionInDB):
    """Reflection data returned in API responses."""
    pass


# Feedback schemas
class FeedbackBase(BaseModel):
    """Base feedback data."""
    feedback_type: str = Field(..., pattern="^(suggestion|bug|compliment)$")
    subject: str = Field(..., max_length=200)
    message: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    contact_email: Optional[EmailStr] = None


class FeedbackCreate(FeedbackBase):
    """Data required to create new feedback."""
    pass


class FeedbackInDB(FeedbackBase):
    """Feedback data as stored in the database."""
    id: UUID
    user_id: UUID
    status: str = "new"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Feedback(FeedbackInDB):
    """Feedback data returned in API responses."""
    pass