from fastapi import APIRouter, UploadFile, File, Depends
from app.core.dependencies import get_current_user, save_upload_file
from app.models import User, Announcement
from app.schemas import AnnouncementResponse
from typing import List

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传文件（图片）"""
    file_url = await save_upload_file(file)
    return {"url": file_url}


@router.get("/announcements", response_model=List[AnnouncementResponse])
async def get_announcements(
    skip: int = 0,
    limit: int = 20,
    #current_user: User = Depends(get_current_user)
):
    """获取公告列表"""
    announcements = await Announcement.filter(is_published=True).order_by("-published_at").offset(skip).limit(limit)
    return announcements


@router.get("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取公告详情"""
    announcement = await Announcement.get_or_none(id=announcement_id, is_published=True)
    if not announcement:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="公告不存在")
    return announcement
