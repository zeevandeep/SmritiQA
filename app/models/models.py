"""
SQLAlchemy database models for the Smriti application.

These models represent the structure of the database tables and their relationships.
They follow the schema defined in the project specifications.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, 
    Boolean, Float, Date, DateTime, ARRAY, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, BYTEA  # Using BYTEA for embeddings
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    """Base user model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String(256), nullable=True)  # Adding password hash
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", uselist=False, back_populates="user")
    sessions = relationship("Session", back_populates="user")
    nodes = relationship("Node", back_populates="user")
    edges = relationship("Edge", back_populates="user")
    reflections = relationship("Reflection", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class UserProfile(Base):
    """User profile information."""
    __tablename__ = "user_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    display_name = Column(Text)
    profile_image_url = Column(Text)  # Google OAuth profile picture URL
    birthdate = Column(Date)
    gender = Column(Text)
    language = Column(Text, default='en')
    language_preference = Column(Text, default='en')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class Session(Base):
    """Journal/voice recording session."""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    duration_seconds = Column(Integer)
    raw_transcript = Column(Text)
    created_at = Column(DateTime, default=func.now())
    is_processed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    nodes = relationship("Node", back_populates="session")


class Node(Base):
    """Atomic cognitive/emotional unit extracted from a session."""
    __tablename__ = "nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    text = Column(Text, nullable=False)
    emotion = Column(Text)
    theme = Column(Text)
    cognition_type = Column(Text)
    embedding = Column(BYTEA)  # For semantic matching, stored as binary data
    created_at = Column(DateTime, default=func.now())
    is_processed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="nodes")
    session = relationship("Session", back_populates="nodes")
    from_edges = relationship("Edge", foreign_keys="Edge.from_node", back_populates="from_node_rel")
    to_edges = relationship("Edge", foreign_keys="Edge.to_node", back_populates="to_node_rel")


class Edge(Base):
    """Connection between nodes representing psychological relationship."""
    __tablename__ = "edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    to_node = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    edge_type = Column(Text, nullable=False)
    match_strength = Column(Float, nullable=False)
    session_relation = Column(Text, nullable=False)
    explanation = Column(Text)
    created_at = Column(DateTime, default=func.now())
    is_processed = Column(Boolean, default=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "edge_type IN ('thought_progression', 'emotion_shift', 'belief_mutation', "
            "'contradiction_loop', 'mixed_transition', 'avoidance_drift', "
            "'recurrence_theme', 'recurrence_emotion', 'recurrence_belief')",
            name="check_edge_type"
        ),
        CheckConstraint(
            "match_strength >= 0 AND match_strength <= 1",
            name="check_match_strength"
        ),
        CheckConstraint(
            "session_relation IN ('intra_session', 'cross_session')",
            name="check_session_relation"
        ),
    )
    
    # Relationships
    user = relationship("User", back_populates="edges")
    from_node_rel = relationship("Node", foreign_keys=[from_node], back_populates="from_edges")
    to_node_rel = relationship("Node", foreign_keys=[to_node], back_populates="to_edges")



class Reflection(Base):
    """AI-generated insight based on nodes and edges for a user."""
    __tablename__ = "reflections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    node_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    edge_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    generated_text = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=func.now())
    is_reflected = Column(Boolean, default=False)
    is_viewed = Column(Boolean, default=False)
    feedback = Column(Integer, nullable=True)
    confidence_score = Column(Float)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="check_confidence_score"
        ),
    )
    
    # Relationships
    user = relationship("User", back_populates="reflections")


class Feedback(Base):
    """User feedback and suggestions."""
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'suggestion', 'bug', 'compliment'
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    contact_email = Column(String(255), nullable=True)  # Optional contact email
    status = Column(String(20), default='new')  # 'new', 'reviewed', 'resolved'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "feedback_type IN ('suggestion', 'bug', 'compliment')",
            name="check_feedback_type"
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="check_rating_range"
        ),
        CheckConstraint(
            "status IN ('new', 'reviewed', 'resolved')",
            name="check_status_values"
        ),
    )
    
    # Relationships
    user = relationship("User", back_populates="feedback")