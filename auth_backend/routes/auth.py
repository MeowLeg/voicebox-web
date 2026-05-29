from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, User, init_db, UserPermission
from auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*roles: str):
    """Dependency factory: only allow users with one of the given roles."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return checker


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    )


@router.post("/register", response_model=LoginResponse)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
):
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少 3 个字符")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 个字符")

    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    import uuid
    user = User(
        id=str(uuid.uuid4()),
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.username})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    db = next(get_db())
    perms = [p.permission for p in db.query(UserPermission).filter_by(user_id=user.id).all()]
    db.close()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "permissions": perms,
    }


def has_permission(perm: str):
    """Dependency: require a specific permission."""
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        has = db.query(UserPermission).filter_by(user_id=user.id, permission=perm).first()
        if not has:
            raise HTTPException(status_code=403, detail=f"需要 {perm} 权限")
        return user
    return checker


AVAILABLE_PERMISSIONS = ["broadcast"]


@router.get("/permissions/available")
def list_available_permissions(user: User = Depends(require_role("admin"))):
    return {"permissions": AVAILABLE_PERMISSIONS}


@router.get("/users")
def list_users(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    for u in users:
        perms = [p.permission for p in db.query(UserPermission).filter_by(user_id=u.id).all()]
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "permissions": perms,
        })
    return {"users": result}


class PermissionGrantRequest(BaseModel):
    permission: str


@router.post("/users/{user_id}/permissions")
def grant_permission(
    user_id: str,
    req: PermissionGrantRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if req.permission not in AVAILABLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="未知的权限类型")
    existing = db.query(UserPermission).filter_by(user_id=user_id, permission=req.permission).first()
    if existing:
        return {"status": "already_granted"}
    import uuid
    perm = UserPermission(id=str(uuid.uuid4()), user_id=user_id, permission=req.permission)
    db.add(perm)
    db.commit()
    return {"status": "granted"}


@router.delete("/users/{user_id}/permissions/{permission}")
def revoke_permission(
    user_id: str,
    permission: str,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    db.query(UserPermission).filter_by(user_id=user_id, permission=permission).delete()
    db.commit()
    return {"status": "revoked"}


class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"


class UserUpdateRequest(BaseModel):
    password: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


@router.post("/users")
def create_user(
    req: UserCreateRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少3个字符")
    if len(req.password) < 3:
        raise HTTPException(status_code=400, detail="密码至少3个字符")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    return {"status": "created", "id": user.id}


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    req: UserUpdateRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.password:
        user.hashed_password = get_password_hash(req.password)
    if req.email is not None:
        user.email = req.email
    if req.role is not None:
        user.role = req.role
    db.commit()
    return {"status": "updated"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    db.delete(target)
    db.commit()
    return {"status": "deleted"}
