from typing import Optional
from beanie import Document
from pydantic import BaseModel
from bson import Regex


class DbModelBase(Document):
    """数据库模型基类"""
    project_id: Optional[str]
    deleted: Optional[bool]

    class Settings:
        indexes = ["project_id", "deleted"]
        bson_encoders = {
            Regex: lambda v: {"$regex": v.pattern},
        }


class CountResult(BaseModel):
    """返回值基类"""
    count: int


class AddResult(BaseModel):
    """返回值基类"""
    id: str
