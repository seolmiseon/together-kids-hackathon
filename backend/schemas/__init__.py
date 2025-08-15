from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# ===== 사용자 스키마 =====
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('비밀번호는 최소 6자 이상이어야 합니다')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None

class User(UserBase):
    id: int
    profile_image: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== 인증 스키마 =====
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# ===== 아파트 스키마 =====
class ApartmentBase(BaseModel):
    name: str
    address: str
    postal_code: Optional[str] = None
    total_households: Optional[int] = None
    facilities: Optional[str] = None

class ApartmentCreate(ApartmentBase):
    pass

class Apartment(ApartmentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== 사용자-아파트 관계 스키마 =====
class UserApartmentBase(BaseModel):
    unit_number: Optional[str] = None

class UserApartmentCreate(UserApartmentBase):
    apartment_id: int

class UserApartment(UserApartmentBase):
    id: int
    apartment_id: int
    is_verified: bool
    role: str
    joined_at: datetime
    apartment: Apartment
    
    class Config:
        from_attributes = True

# ===== 아이 프로필 스키마 =====
class ChildBase(BaseModel):
    name: str
    birth_date: datetime
    gender: Optional[str] = None
    special_notes: Optional[str] = None
    emergency_contact: Optional[str] = None

class ChildCreate(ChildBase):
    pass

class ChildUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    profile_image: Optional[str] = None
    special_notes: Optional[str] = None
    emergency_contact: Optional[str] = None

class Child(ChildBase):
    id: int
    parent_id: int
    profile_image: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ===== 일정 스키마 =====
class ScheduleBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    schedule_type: str
    priority: str = "normal"
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    reminder_minutes: int = 30

class ScheduleCreate(ScheduleBase):
    child_id: int

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    schedule_type: Optional[str] = None
    priority: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    reminder_minutes: Optional[int] = None
    is_completed: Optional[bool] = None

class Schedule(ScheduleBase):
    id: int
    child_id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    child: Child
    
    class Config:
        from_attributes = True

# ===== 게시글 스키마 =====
class PostBase(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[str] = None
    image_urls: Optional[str] = None
    is_emergency: bool = False

class PostCreate(PostBase):
    apartment_id: int

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    image_urls: Optional[str] = None

class Post(PostBase):
    id: int
    author_id: int
    apartment_id: int
    views: int
    likes: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    author: User
    apartment: Apartment
    
    class Config:
        from_attributes = True

# ===== 댓글 스키마 =====
class CommentBase(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None

class CommentCreate(CommentBase):
    post_id: int

class CommentUpdate(BaseModel):
    content: str

class Comment(CommentBase):
    id: int
    post_id: int
    author_id: int
    likes: int
    created_at: datetime
    updated_at: datetime
    author: User
    
    class Config:
        from_attributes = True

# ===== 응답 스키마 =====
class MessageResponse(BaseModel):
    message: str
    data: Optional[dict] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int
