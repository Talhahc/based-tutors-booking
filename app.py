import os
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("BOOKING_DATABASE", ROOT / "booking.sqlite3"))


@asynccontextmanager
async def lifespan(app):
    with closing(sqlite3.connect(DATABASE)) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY,
                starts_at TEXT NOT NULL UNIQUE,
                student_name TEXT,
                version INTEGER NOT NULL DEFAULT 0
            )
        """)
    yield


app = FastAPI(title="Based Tutors Booking", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))

NOTICES = {
    "added": "Slot added.",
    "booked": "Session booked.",
    "cancelled": "Booking cancelled. The slot is available again.",
}


def render_schedule(request, message=None, status_code=200):
    now = datetime.now()
    with closing(sqlite3.connect(DATABASE)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT * FROM slots WHERE starts_at > ? ORDER BY starts_at",
            (now.isoformat(timespec="minutes"),),
        ).fetchall()

    slots = []
    for row in rows:
        start = datetime.fromisoformat(row["starts_at"])
        slots.append({
            **dict(row),
            "day_label": f"{start:%a} {start.day} {start:%b %Y}",
            "time_label": start.strftime("%H:%M"),
        })

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "slots": slots,
            "message": message,
            "minimum_date": now.date().isoformat(),
            "is_error": status_code >= 400,
        },
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def schedule(request: Request):
    return render_schedule(request, NOTICES.get(request.query_params.get("notice")))


@app.post("/slots")
def add_slot(request: Request, slot_date: str = Form(""), slot_time: str = Form("")):
    try:
        start = datetime.strptime(f"{slot_date}T{slot_time}", "%Y-%m-%dT%H:%M")
    except ValueError:
        return render_schedule(request, "Choose a valid date and start time.", 400)

    if start.minute not in (0, 30) or start <= datetime.now():
        return render_schedule(request, "Choose a future start time on the hour or half-hour.", 400)

    with closing(sqlite3.connect(DATABASE)) as db, db:
        result = db.execute(
            "INSERT INTO slots (starts_at) VALUES (?) ON CONFLICT(starts_at) DO NOTHING",
            (start.isoformat(timespec="minutes"),),
        )

    if result.rowcount == 0:
        return render_schedule(request, "A slot already exists at that time.", 409)
    return RedirectResponse("/?notice=added", status_code=303)


@app.post("/slots/{slot_id}/book")
def book_slot(request: Request, slot_id: int, version: int = Form(), student_name: str = Form("")):
    name = student_name.strip()
    if not 1 <= len(name) <= 80:
        return render_schedule(request, "Enter a student name between 1 and 80 characters.", 400)

    with closing(sqlite3.connect(DATABASE)) as db, db:
        # SQLite checks availability and changes the slot in the same statement.
        result = db.execute("""
            UPDATE slots
            SET student_name = ?, version = version + 1
            WHERE id = ? AND version = ? AND student_name IS NULL AND starts_at > ?
        """, (name, slot_id, version, datetime.now().isoformat(timespec="minutes")))

    if result.rowcount == 0:
        return render_schedule(request, "That slot has changed or is no longer available.", 409)
    return RedirectResponse("/?notice=booked", status_code=303)


@app.post("/slots/{slot_id}/cancel")
def cancel_booking(request: Request, slot_id: int, version: int = Form()):
    with closing(sqlite3.connect(DATABASE)) as db, db:
        result = db.execute("""
            UPDATE slots
            SET student_name = NULL, version = version + 1
            WHERE id = ? AND version = ? AND student_name IS NOT NULL AND starts_at > ?
        """, (slot_id, version, datetime.now().isoformat(timespec="minutes")))

    if result.rowcount == 0:
        return render_schedule(request, "That booking has changed or is no longer upcoming.", 409)
    return RedirectResponse("/?notice=cancelled", status_code=303)
