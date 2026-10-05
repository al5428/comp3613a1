from typing import Optional

from app.repositories.user import UserRepository
from app.repositories.volunteer_submission import AdministratorRepository, StudentRepository
from app.schemas.user import RegularUserCreate
from app.utilities.security import create_access_token, encrypt_password, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=password, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(self, username: str, email: str, password: str):
        new_user = RegularUserCreate(
            username=username,
            email=email,
            password=encrypt_password(password),
        )
        user = self.user_repo.create(new_user)
        if user.role == "admin":
            AdministratorRepository(self.user_repo.db).get_or_create_for_user(user)
        else:
            StudentRepository(self.user_repo.db).get_or_create_for_user(user)
        return user
