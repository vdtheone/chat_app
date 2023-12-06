from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from config import Base


class ChatGroup(Base):
    __tablename__ = 'chat_group'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(String(255))
    created_by = Column(Integer, ForeignKey('users.id'))  
    created_at = Column(DateTime, server_default=func.now(), index=True)
    last_activity = Column(DateTime)


class GroupMembership(Base):
    __tablename__ = 'group_membership'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('chat_group.id'))
    user_id = Column(Integer, ForeignKey('users.id'))  

