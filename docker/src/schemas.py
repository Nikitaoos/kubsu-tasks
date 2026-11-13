from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Имя: обрезаем пробелы по краям, не пустое, не длиннее 100 символов.
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class UserCreate(BaseModel):
    name: Name


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
