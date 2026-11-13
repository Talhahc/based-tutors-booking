# Based Tutors Booking

A local booking prototype for one tutor. Add a 30-minute slot, book it under a student name, or cancel a booking to make the slot available again. The schedule uses the computer’s local time.

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

## Explain it in an interview

> I wanted one place for a tutor to manage their available sessions. I modelled each slot as a row in SQLite. An empty `student_name` means the slot is available. Clicking Book sends an HTML form to FastAPI, which runs one SQL update that only succeeds while the slot is still available. If two requests go for the same slot, the first updates the row and the second updates zero rows. The app shows a message asking the user to check the schedule.

- `UNIQUE` on `starts_at` keeps the tutor from adding the same slot twice.
- `student_name IS NULL` is part of the booking update. SQLite checks that condition as it applies the change, so two requests cannot both claim the same available slot.
- `version` is a counter that increases whenever a slot is booked or cancelled. The form carries the version the user saw, so a cancellation from an old page cannot clear someone else’s newer booking.
- After a successful change the browser returns to the schedule. Refreshing then reloads the page without sending the form again.

## Try the race condition yourself

1. Add an available slot. Open the schedule in two tabs before either tab books it.
2. Book it for Alex in the first tab. In the second tab, try booking the same slot for Sam.
3. The second tab should show a conflict message and Alex should still hold the slot. Cancel Alex’s booking and confirm the slot becomes available again.
