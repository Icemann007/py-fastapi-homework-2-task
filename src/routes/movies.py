from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieUpdateSchema, MovieCreateSchema, MovieBase

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        *,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
        db: Annotated[AsyncSession, Depends(get_db)],
):
    quantity = await db.execute(select(func.count(MovieModel.id)))
    total_items = quantity.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    movie_per_page = await db.execute(
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    )
    movies = movie_per_page.scalars().all()

    movies_list = [MovieBase.model_validate(movie) for movie in movies]

    base_path = "/theater/movies/"

    return MovieListResponseSchema(
        movies=movies_list,
        prev_page=f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: Annotated[AsyncSession, Depends(get_db)]):
    name_and_date_result = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    name_and_date = name_and_date_result.scalar_one_or_none()

    if name_and_date:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country_result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_result.scalar_one_or_none()

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for genre_name in movie.genres:
        genre_result = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
        genre = genre_result.scalar_one_or_none()

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)

        genres.append(genre)
    await db.flush()

    actors = []
    for actor_name in movie.actors:
        actor_result = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
        actor = actor_result.scalar_one_or_none()

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)

        actors.append(actor)
    await db.flush()

    languages = []
    for language_name in movie.languages:
        language_result = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
        language = language_result.scalar_one_or_none()

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)

        languages.append(language)
    await db.flush()

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie, attribute_names=["genres", "actors", "languages", "country"])
    return MovieDetailSchema.model_validate(new_movie)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        movie_id: Annotated[int, Path()],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: Annotated[int, Path()],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: Annotated[int, Path()],
        update_film: MovieUpdateSchema,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for field, value in update_film.model_dump().items():
        if value is not None:
            setattr(movie, field, value)

    await db.commit()
    await db.refresh(movie)
    return {"detail": "Movie updated successfully."}
