from typing import TypeVar, Optional
from beanie.odm.queries.find import FindMany
from beanie.operators import In, Or
from bson import ObjectId, json_util
from pydantic import BaseModel
from fastapi_mongo_crud.exceptions import CrudException
from fastapi_mongo_crud.models import DbModelBase

TDbModel = TypeVar('TDbModel', bound=DbModelBase)


async def find(query: FindMany[TDbModel], project_id: str = None, page_size: int = 0, page_num: int = 0,
               filter_str: str = "", order_str: str = "", include_shared=False) -> list[TDbModel]:
    """批量查询的工具函数"""
    query = make_query(query, project_id, page_size, page_num,
                       filter_str, order_str, include_shared)
    return await query.to_list()


async def count(query: FindMany[TDbModel], project_id: str = None, filter_str: str = "",
                include_shared=False) -> int:
    """获取数量的工具函数"""
    query = make_query(query, project_id, 0, 0, filter_str, "", include_shared)
    return await query.count()


async def find_one(query: FindMany[TDbModel], project_id: str = None,
                   include_shared=False, no_raise=False) -> TDbModel:
    """按id查询单条数据的工具函数"""
    query = make_query(query, project_id, include_shared=include_shared)
    db_data: Optional[TDbModel] = await query.first_or_none()
    if db_data is None and not no_raise:
        raise CrudException("找不到数据")
    return db_data


async def add(data: TDbModel, project_id: str = None, existed: FindMany[TDbModel] = None) -> str:
    """添加数据的工具函数"""
    if existed:
        await raise_if_exists(existed.find({"id": data.id, "deleted": {"$ne": True}}), project_id)
    data.project_id = project_id
    await data.insert()
    return str(data.id)


async def update(update_dict: dict, query: FindMany[TDbModel], project_id: str = None,
                 existed: FindMany[TDbModel] = None):
    """更新数据的工具函数"""
    db_data = await find_one(query, project_id)
    if existed:
        await raise_if_exists(existed.find({"id": db_data.id, "deleted": {"$ne": True}}), project_id)
    await db_data.update({"$set": update_dict})


async def remove(query: FindMany[TDbModel], project_id: str = None, fake_delete=False, no_raise=False):
    """删除数据的工具函数"""
    db_data = await find_one(query, project_id, no_raise=no_raise)
    if db_data is None:
        return
    if fake_delete:
        await db_data.update({"$set": {"deleted": True}})
    else:
        await db_data.delete()


async def raise_if_exists(query: FindMany[DbModelBase], project_id: str = None, include_shared=False):
    """如果数据已存在则抛出异常"""
    query = make_query(query, project_id, include_shared=include_shared)
    if await query.count() > 0:
        raise CrudException("数据已存在")


def make_query(query: FindMany[TDbModel], project_id: str = None, page_size: int = 0, page_num: int = 0,
               filter_str: str = "", order_str: str = "", include_shared=False) -> FindMany[TDbModel]:
    """构造查询的工具函数"""
    query = query.find({"deleted": {"$ne": True}})
    if project_id:
        if include_shared:
            query = query.find(Or(DbModelBase.project_id == project_id, DbModelBase.project_id == "shared"))
        else:
            query = query.find(DbModelBase.project_id == project_id)
    if len(filter_str) > 0:
        query = query.find((json_util.loads(filter_str)))
    if len(order_str) > 0:
        query = query.sort(*order_str.split(","))
    if page_size > 0:
        query = query.skip(page_num * page_size).limit(page_size)
    return query


async def add_name(data: list[BaseModel], id_field: str, name_field: str, query: FindMany[DbModelBase],
                   override_join_name_field: str = 'name'):
    """根据数据中的xx_id字段，添加xx_name字段"""
    id_list = [ObjectId(getattr(d, id_field)) for d in data]
    db_data = await query.find(In(DbModelBase.id, id_list)).to_list()
    names = {d.id: getattr(d, override_join_name_field) for d in db_data}
    for d in data:
        setattr(d, name_field, names.get(ObjectId(getattr(d, id_field))))


async def add_name_list(data: list[BaseModel], ids_field: str, names_field: str, query: FindMany[DbModelBase]):
    """根据数据中的xx_ids字段，添加xx_names字段"""
    id_list = [ObjectId(id) for d in data if getattr(d, ids_field) for id in getattr(d, ids_field)]
    db_data = await query.find(In(DbModelBase.id, id_list)).to_list()
    names = {d.id: getattr(d, 'name') for d in db_data}
    for d in data:
        if getattr(d, ids_field):
            setattr(d, names_field, [names.get(ObjectId(id)) for id in getattr(d, ids_field)])
