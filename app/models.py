from datetime import datetime
from sqlalchemy import String,Integer,Float,Text,DateTime,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .database import Base
class User(Base):
    __tablename__='users'; id:Mapped[int]=mapped_column(Integer,primary_key=True); name:Mapped[str]=mapped_column(String(120)); email:Mapped[str]=mapped_column(String(255),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); recommendations=relationship('Recommendation',back_populates='user',cascade='all, delete-orphan')
class Recommendation(Base):
    __tablename__='recommendations'; id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey('users.id')); planner_type:Mapped[str]=mapped_column(String(30)); budget:Mapped[float]=mapped_column(Float); input_summary:Mapped[str]=mapped_column(Text); result_json:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); user=relationship('User',back_populates='recommendations')
