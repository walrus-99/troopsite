from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from starlette.datastructures import FormData

from .database import create_db_and_tables, get_db
from .models import Grade, Member, Parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Troopsite", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="troopsite/static"), name="static")

templates = Jinja2Templates(directory="troopsite/templates")


DbSession = Annotated[Session, Depends(get_db)]


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _ids_from_form(form: FormData, field_name: str) -> list[int]:
    return [int(value) for value in form.getlist(field_name) if value]


def _roster_context(request: Request, db: Session) -> dict[str, object]:
    parents = db.scalars(
        select(Parent)
        .options(selectinload(Parent.members))
        .order_by(Parent.last_name, Parent.first_name)
    ).all()
    members = db.scalars(
        select(Member)
        .options(selectinload(Member.parents))
        .order_by(Member.last_name, Member.first_name)
    ).all()

    return {"request": request, "parents": parents, "members": members, "grades": list(Grade)}


def _roster_tables(request: Request, db: Session) -> HTMLResponse:
    return templates.TemplateResponse(request, "_roster_tables.html", _roster_context(request, db))


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: DbSession):
    parent_count = db.scalar(select(func.count()).select_from(Parent))
    member_count = db.scalar(select(func.count()).select_from(Member))

    return templates.TemplateResponse(
        request,
        "index.html",
        {"parent_count": parent_count or 0, "member_count": member_count or 0},
    )


@app.get("/roster", response_class=HTMLResponse)
def roster(request: Request, db: DbSession):
    return templates.TemplateResponse(request, "roster.html", _roster_context(request, db))


@app.post("/roster/parents")
async def create_parent(request: Request, db: DbSession):
    form = await request.form()
    parent = Parent(
        first_name=str(form["first_name"]).strip(),
        last_name=str(form["last_name"]).strip(),
        primary_email=_optional(str(form.get("primary_email") or "")),
        secondary_email=_optional(str(form.get("secondary_email") or "")),
        primary_phone=_optional(str(form.get("primary_phone") or "")),
        secondary_phone=_optional(str(form.get("secondary_phone") or "")),
    )
    parent.members = db.scalars(select(Member).where(Member.id.in_(_ids_from_form(form, "member_ids")))).all()
    db.add(parent)
    db.commit()
    return RedirectResponse("/roster", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/roster/parents/{parent_id}/edit", response_class=HTMLResponse)
def edit_parent(parent_id: int, request: Request, db: DbSession):
    parent = db.get(Parent, parent_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent not found")

    context = _roster_context(request, db)
    context["parent"] = parent
    return templates.TemplateResponse(request, "edit_parent.html", context)


@app.post("/roster/parents/{parent_id}/edit")
async def update_parent(parent_id: int, request: Request, db: DbSession):
    parent = db.get(Parent, parent_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent not found")

    form = await request.form()
    parent.first_name = str(form["first_name"]).strip()
    parent.last_name = str(form["last_name"]).strip()
    parent.primary_email = _optional(str(form.get("primary_email") or ""))
    parent.secondary_email = _optional(str(form.get("secondary_email") or ""))
    parent.primary_phone = _optional(str(form.get("primary_phone") or ""))
    parent.secondary_phone = _optional(str(form.get("secondary_phone") or ""))
    parent.members = db.scalars(select(Member).where(Member.id.in_(_ids_from_form(form, "member_ids")))).all()
    db.commit()
    return RedirectResponse("/roster", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/roster/parents/{parent_id}/members/{member_id}/unlink", response_class=HTMLResponse)
def unlink_member_from_parent(parent_id: int, member_id: int, request: Request, db: DbSession):
    parent = db.get(Parent, parent_id)
    member = db.get(Member, member_id)
    if parent is None or member is None:
        raise HTTPException(status_code=404, detail="Roster link not found")

    if member in parent.members:
        parent.members.remove(member)
        db.commit()

    return _roster_tables(request, db)


@app.post("/roster/members")
async def create_member(request: Request, db: DbSession):
    form = await request.form()
    member = Member(
        first_name=str(form["first_name"]).strip(),
        last_name=str(form["last_name"]).strip(),
        age=int(str(form["age"])),
        grade=Grade(str(form["grade"])),
    )
    member.parents = db.scalars(select(Parent).where(Parent.id.in_(_ids_from_form(form, "parent_ids")))).all()
    db.add(member)
    db.commit()
    return RedirectResponse("/roster", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/roster/members/{member_id}/edit", response_class=HTMLResponse)
def edit_member(member_id: int, request: Request, db: DbSession):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    context = _roster_context(request, db)
    context["member"] = member
    return templates.TemplateResponse(request, "edit_member.html", context)


@app.post("/roster/members/{member_id}/edit")
async def update_member(member_id: int, request: Request, db: DbSession):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    form = await request.form()
    member.first_name = str(form["first_name"]).strip()
    member.last_name = str(form["last_name"]).strip()
    member.age = int(str(form["age"]))
    member.grade = Grade(str(form["grade"]))
    member.parents = db.scalars(select(Parent).where(Parent.id.in_(_ids_from_form(form, "parent_ids")))).all()
    db.commit()
    return RedirectResponse("/roster", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/roster/members/{member_id}/parents/{parent_id}/unlink", response_class=HTMLResponse)
def unlink_parent_from_member(member_id: int, parent_id: int, request: Request, db: DbSession):
    member = db.get(Member, member_id)
    parent = db.get(Parent, parent_id)
    if member is None or parent is None:
        raise HTTPException(status_code=404, detail="Roster link not found")

    if parent in member.parents:
        member.parents.remove(parent)
        db.commit()

    return _roster_tables(request, db)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/httpx-example")
async def httpx_example() -> dict[str, object]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("https://httpbin.org/json")
        response.raise_for_status()

    return {"source": "httpbin", "data": response.json()}
