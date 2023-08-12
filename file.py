from fastapi import APIRouter, Depends, UploadFile, Form, File
from fastapi.responses import RedirectResponse
import aioboto3
import uuid
from urllib import parse
from fastapi_mongo_crud import *

file_router = APIRouter(tags=["file"], prefix="/api/v1/project/{project_id}/file")


@file_router.post("/upload", dependencies=[Depends(login_required)])
async def upload(file: UploadFile, project_id: str):
    key = f"upload/{project_id}/{uuid.uuid4()}/{file.filename}"
    async with make_s3_client() as client:
        await client.upload_fileobj(file.file, settings.FILE_BUCKET, key)
    return f"/api/v1/project/{project_id}/file/download?key={parse.quote(key)}"


@file_router.get("/download")
async def download(project_id: str, key: str):
    if not key.startswith(f"upload/{project_id}/"):
        raise Exception("无权限")
    async with make_s3_client() as client:
        return RedirectResponse(
            await client.generate_presigned_url('get_object', Params={'Bucket': settings.FILE_BUCKET, 'Key': key}))


def make_s3_client():
    return aioboto3.Session().client('s3', endpoint_url=settings.FILE_ENDPOINT,
                                     aws_access_key_id=settings.FILE_KEY,
                                     aws_secret_access_key=settings.FILE_SECRET)
