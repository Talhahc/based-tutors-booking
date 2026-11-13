# Based Tutors Booking

An AI-assisted booking prototype for Based Tutors, built with Python, FastAPI and SQLite. It gives one tutor a page to add 30-minute slots, book lessons and reopen cancelled slots. It runs locally and uses the computer’s time zone.

## Run it

From this project folder, with Python 3.11 or later installed, run these commands in a Mac or Linux terminal. Check `python3 --version` first. If it points to an older version, use the command for your newer installation, such as `python3.12`, to create the virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser. Pick a future date and a time ending in `:00` or `:30`. Use a sample name to try booking. Press `Ctrl+C` in the terminal to stop the server. SQLite creates `booking.sqlite3` on the first run and keeps the schedule between runs.

## Read the code

| File | What it does |
| --- | --- |
| `app.py` | Receives forms, validates input, and reads or updates the database. |
| `templates/index.html` | Displays the schedule and the three HTML forms. |
| `static/style.css` | Styles the page. |

## How booking works

Each slot is one SQLite row. When the booking form is submitted, FastAPI runs a single SQL update that sets the student name only if the slot is still available and the form’s version matches the row. When two requests compete for the same slot, one updates the row and the other receives an HTTP 409 conflict. A test with two simultaneous requests confirmed this behaviour.

The database also enforces unique start times. The version increases after each booking or cancellation, so an old form cannot cancel a newer booking.

## Try it in two tabs

1. Add an available slot. Open the schedule in two tabs before either tab books it.
2. Book it for Alex in the first tab. In the second tab, try booking the same slot for Sam.
3. The second tab should show a conflict message and Alex should still hold the slot. Cancel Alex’s booking and confirm the slot becomes available again.
