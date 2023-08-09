from typing import Optional
from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from fastapi.security import HTTPBearer

from .models import TokenDetail


def login_required(project_id: Optional[str] = None, jwt: AuthJWT = Depends(), b=Depends(HTTPBearer())):
    """用于声明某个接口需要登录，返回一个对象，包含用户的基本信息"""
    # b这个参数不能删掉，否则fastapi不知道我们需要用到HTTPBearer
    jwt.jwt_required()
    token = TokenDetail(**jwt.get_raw_jwt())
    if token.project_id != project_id and not token.is_root:
        raise HTTPException(status_code=404, detail="project_id不匹配")
    return token


def auth_required(auth: str):
    """用于声明某个接口需要什么权限，如果没有这个权限则报错，会返回该用户基本信息"""

    # 这是一个装饰器写法，返回一个函数，调用的时候形式如 Depends(auth_required(Auth.项目管理))
    def function(token: TokenDetail = Depends(login_required)):
        if not token.is_root and auth not in token.auths:
            raise HTTPException(status_code=401, detail="没有权限：" + auth)
        return token

    return function


def root_required(jwt: AuthJWT = Depends(), b=Depends(HTTPBearer())):
    jwt.jwt_required()
    if not jwt.get_raw_jwt()["is_root"]:
        raise HTTPException(status_code=401, detail="需要超级管理员权限")
