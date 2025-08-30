from datetime import date, datetime, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class CountryBase(BaseModel):
    id: int
    code: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)


class GenreBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ActorBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class LanguageBase(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieBase]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    def max_year_date(cls, value):
        max_date = datetime.now().date() + timedelta(days=365)

        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")

        return value


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryBase
    genres: list[GenreBase]
    actors: list[ActorBase]
    languages: list[LanguageBase]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    date: Optional[date] = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)
    country: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    languages: list[str] | None = None

    @field_validator("date")
    def max_year_date(cls, value):
        if value is None:
            return value

        max_date = datetime.now().date() + timedelta(days=365)
        if value > max_date:
            raise ValueError("The date must not be more than one year in the future.")

        return value
