"""
Announcement endpoints for the High School Management System API
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException, Query

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def _require_signed_in_user(username: Optional[str]) -> Dict[str, Any]:
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _parse_date_field(field_name: str, value: Optional[str], required: bool = False) -> Optional[str]:
    if value is None or value == "":
        if required:
            raise HTTPException(status_code=400, detail=f"{field_name} is required")
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be in YYYY-MM-DD format"
        ) from exc


def _normalize_message(message: Optional[str]) -> str:
    clean_message = (message or "").strip()
    if not clean_message:
        raise HTTPException(status_code=400, detail="message is required")
    if len(clean_message) > 500:
        raise HTTPException(status_code=400, detail="message must be 500 characters or fewer")
    return clean_message


def _serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(announcement["_id"]),
        "message": announcement["message"],
        "start_date": announcement.get("start_date"),
        "expiration_date": announcement["expiration_date"],
        "created_by": announcement.get("created_by"),
        "created_at": announcement.get("created_at"),
        "updated_by": announcement.get("updated_by"),
        "updated_at": announcement.get("updated_at")
    }


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get currently active announcements for public display."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": None},
            {"start_date": ""},
            {"start_date": {"$lte": today}}
        ]
    }

    results = announcements_collection.find(query).sort([
        ("expiration_date", 1),
        ("_id", -1)
    ])
    return [_serialize_announcement(announcement) for announcement in results]


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_all_announcements(
    teacher_username: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    """Get all announcements for management (requires sign-in)."""
    _require_signed_in_user(teacher_username)

    results = announcements_collection.find({}).sort([
        ("expiration_date", 1),
        ("_id", -1)
    ])
    return [_serialize_announcement(announcement) for announcement in results]


@router.post("", response_model=Dict[str, Any])
def create_announcement(
    teacher_username: Optional[str] = Query(None),
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Create a new announcement (requires sign-in)."""
    _require_signed_in_user(teacher_username)

    message = _normalize_message(payload.get("message"))
    start_date = _parse_date_field("start_date", payload.get("start_date"), required=False)
    expiration_date = _parse_date_field("expiration_date", payload.get("expiration_date"), required=True)

    if start_date and start_date > expiration_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to expiration_date")

    now = datetime.utcnow().isoformat()
    document = {
        "message": message,
        "expiration_date": expiration_date,
        "start_date": start_date,
        "created_by": teacher_username,
        "created_at": now,
        "updated_by": teacher_username,
        "updated_at": now
    }

    result = announcements_collection.insert_one(document)
    created = announcements_collection.find_one({"_id": result.inserted_id})
    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Update an existing announcement (requires sign-in)."""
    _require_signed_in_user(teacher_username)

    message = _normalize_message(payload.get("message"))
    start_date = _parse_date_field("start_date", payload.get("start_date"), required=False)
    expiration_date = _parse_date_field("expiration_date", payload.get("expiration_date"), required=True)

    if start_date and start_date > expiration_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to expiration_date")

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "message": message,
                "start_date": start_date,
                "expiration_date": expiration_date,
                "updated_by": teacher_username,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": object_id})
    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement (requires sign-in)."""
    _require_signed_in_user(teacher_username)

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
