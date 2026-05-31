import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(10), default='user')
    score = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    avatar = Column(String(256), default='')
    bio = Column(Text, default='')

class Challenge(Base):
    __tablename__ = 'challenges'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)
    difficulty = Column(Integer, default=1)
    score = Column(Integer, default=100)
    flag = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    hints = Column(Text, default='')
    attachment_url = Column(String(500), default='')
    docker_image = Column(String(200), default='')
    is_dynamic = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    max_attempts = Column(Integer, default=0)
    solves_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Solve(Base):
    __tablename__ = 'solves'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    challenge_id = Column(Integer, ForeignKey('challenges.id'))
    solved_at = Column(DateTime, default=datetime.datetime.utcnow)
    score_awarded = Column(Integer, default=0)

class LabInstance(Base):
    __tablename__ = 'lab_instances'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    challenge_id = Column(Integer, ForeignKey('challenges.id'))
    container_id = Column(String(128), default='')
    host_port = Column(Integer, default=0)
    status = Column(String(20), default='stopped')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    challenge_id = Column(Integer, ForeignKey('challenges.id'))
    flag_input = Column(String(500))
    is_correct = Column(Boolean, default=False)
    ip_address = Column(String(50), default='')
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
