from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    profile_image = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    apartments = relationship("UserApartment", back_populates="user")
    children = relationship("Child", back_populates="parent")
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

class Apartment(Base):
    """아파트 단지 모델"""
    __tablename__ = "apartments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text, nullable=False)
    postal_code = Column(String(10), nullable=True)
    total_households = Column(Integer, nullable=True)
    facilities = Column(Text, nullable=True)  # JSON 형태로 저장
    created_at = Column(DateTime, server_default=func.now())
    
    # 관계설정
    user_apartments = relationship("UserApartment", back_populates="apartment")
    posts = relationship("Post", back_populates="apartment")

class UserApartment(Base):
    """사용자-아파트 관계 모델 (다대다)"""
    __tablename__ = "user_apartments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=False)
    unit_number = Column(String(20), nullable=True)  # 동호수
    is_verified = Column(Boolean, default=False)  # 거주 인증 여부
    role = Column(String(20), default="resident")  # resident, admin
    joined_at = Column(DateTime, server_default=func.now())
    
    # 관계설정
    user = relationship("User", back_populates="apartments")
    apartment = relationship("Apartment", back_populates="user_apartments")

class Child(Base):
    """아이 프로필 모델"""
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    birth_date = Column(DateTime, nullable=False)
    gender = Column(String(10), nullable=True)  # male, female, other
    profile_image = Column(String(500), nullable=True)
    special_notes = Column(Text, nullable=True)  # 특이사항, 알레르기 등
    emergency_contact = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    parent = relationship("User", back_populates="children")
    schedules = relationship("Schedule", back_populates="child")

class Schedule(Base):
    """아이 일정 모델"""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    schedule_type = Column(String(50), nullable=False)  # activity, meal, sleep, medical, etc.
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100), nullable=True)  # daily, weekly, monthly
    reminder_minutes = Column(Integer, default=30)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    child = relationship("Child", back_populates="schedules")

class Post(Base):
    """커뮤니티 게시글 모델"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # general, event, question, tip, emergency
    tags = Column(Text, nullable=True)  # JSON 배열로 저장
    image_urls = Column(Text, nullable=True)  # JSON 배열로 저장
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    author = relationship("User", back_populates="posts")
    apartment = relationship("Apartment", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    """댓글 모델"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # 대댓글용
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", remote_side=[id])  # 자기참조
    
    
class SafeZone(Base):
    """안전구역 모델"""
    __tablename__ = "safe_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    name = Column(String(100), nullable=False)  # "집", "어린이집", "학원" 등
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Integer, default=100)  # 미터 단위
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 관계설정
    user = relationship("User")
    child = relationship("Child")
