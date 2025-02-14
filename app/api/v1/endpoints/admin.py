from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.crud.user import user
from app.crud.article import article
from app.schemas.user import User
from app.schemas.article import Article
from app.db.session import get_db
from app.core.deps import get_current_admin_user

router = APIRouter()

@router.get("/users", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Retrieve users. Only accessible by admin users.
    """
    users = user.get_multi(db, skip=skip, limit=limit)
    return users

@router.put("/users/{user_id}/toggle-admin", response_model=User)
def toggle_admin_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Toggle admin status of a user. Only accessible by admin users.
    """
    db_user = user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot modify their own admin status"
        )
    
    return user.update(db, db_obj=db_user, obj_in={"is_admin": not db_user.is_admin})

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete user. Only accessible by admin users.
    """
    db_user = user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot delete themselves"
        )
    
    user.remove(db, id=user_id)
    return {"message": "User deleted successfully"}