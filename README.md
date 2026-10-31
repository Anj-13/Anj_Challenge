# Medicine Tracker

![Language](https://img.shields.io/badge/Language-Python%20%7C%20JavaScript-blue)
![Framework](https://img.shields.io/badge/Framework-FastAPI-009688)
![Status](https://img.shields.io/badge/Status-Learning%20Project-informational)

**An interview coding challenge revisited and improved as an independent software engineering learning project.**

Medicine Tracker is a small full-stack app for viewing, adding, updating and deleting medicine prices, with a report of the average price. A plain JavaScript frontend talks to a Python FastAPI backend, which stores its records in a JSON file. The original version came from an unsuccessful technical interview challenge. This version keeps the same app and stack, and fixes the problems I found when I reviewed my own work.

> **Disclaimer:** All medicines in `backend/data.json` are fictional and do not represent real medicines.

## Table of Contents

- [Project Overview](#project-overview)
- [Technical Implementation](#technical-implementation)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [System Architecture & Project Structure](#system-architecture--project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Testing & Quality](#testing--quality)
- [Challenges & Solutions](#challenges--solutions)
- [Results & What I Learned](#results--what-i-learned)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)
- [License](#license)

## Project Overview

**Original challenge:** In November 2025 I completed the Eli Lilly student software engineer placement take-home challenge. The [starter repository](https://github.com/SamThompson95/lilly-recruitment-challenge) provided the core API and a sample database with deliberate gaps, including a blank name and a missing price. The task was to build the frontend and cope with the incomplete data. The submission was not successful.

**Why I revisited it:** I wanted to go back to my own code with more experience, find out what was really wrong with it, and fix it properly. This is no longer an active interview submission.

**Problem:** A review found that the app looked finished but was unreliable. The API accepted invalid prices, records could only be targeted by name, and the frontend could not show any success or error message at all.

**Solution:** I kept the existing app and stack, and repaired it. Records now have stable IDs, the API validates input and returns accurate status codes, the frontend reports what actually happened, and the repository holds only what the app needs.

**Project Status:** Completed as a learning project. It runs locally and is not deployed.

## Technical Implementation

Developed by [Anj-13](https://github.com/Anj-13), building on the [challenge starter repository](https://github.com/SamThompson95/lilly-recruitment-challenge).

**Original challenge work**
- Built the interface in plain HTML, CSS and JavaScript, using `fetch` and `FormData` to connect it to the API.
- Added the `GET /average-price` report, which leaves missing and invalid prices out of the calculation.
- Added fallback labels so that incomplete records still display.

**Backend improvements**
- Gave every record a stable ID, and added a migration that only adds the `id` field and backs up the original file.
- Added validation for names and prices in one place, including rejecting `nan` and `inf`.
- Replaced `200` responses containing an error with real `404`, `409`, `422` and `500` responses.
- Made file access safer with a lock around each read and write, and atomic saves.
- Made the data path independent of the folder the server is started from.

**Frontend improvements**
- Added one request function that treats any non-2xx response as a failure.
- Restored the notification system, which had been deleted while nine calls to it remained.
- Replaced the free-text name fields on the update and delete forms with dropdowns keyed by ID.
- Redesigned the layout with loading states, inline validation and automatic report refreshes.

**Repository and tooling**
- Rewrote `start.bat`, `start.ps1` and `start.sh` so they share one virtual environment location, report errors clearly, and only install dependencies when `requirements.txt` changes.
- Removed the unused Express dependency and 584 tracked `node_modules` files.
- Added a regression test suite for the API.

## Key Features

- **Medicine list:** See every medicine with its price, newest first.
- **Clear handling of missing data:** Incomplete records appear as "Unknown Med" or "Price: Not Available" and are highlighted.
- **Add, update and delete:** Forms validate input before sending it and show errors beside the field.
- **Quick actions:** Quick Update fills in the update form for a record, and Quick Delete removes one after a confirmation prompt.
- **Accurate feedback:** Success messages appear only after the API confirms a change, and failures show the reason.
- **Quarterly report:** See the average price and how many medicines it covers. It refreshes after every change.
- **Responsive design:** The layout adapts from desktop down to a 320px mobile width.

## Tech Stack

| Layer | Technologies | Purpose |
| --- | --- | --- |
| Frontend / UI | HTML, CSS, JavaScript | Page structure, styling and browser logic |
| Backend / Core | Python, FastAPI, Uvicorn | REST API and development server |
| Database / Storage | JSON file (`backend/data.json`) | Stores medicine records |
| APIs | Fetch API, FormData | Sends requests from the browser to the backend |
| Tools / Testing | Git, pytest, Postman, VS Code | Version control, API testing and development |

## System Architecture & Project Structure

The browser loads a static page, and `script.js` calls the API on `localhost:8000`. FastAPI reads and writes `data.json` on each request.

```text
frontend (HTML, CSS, JS)  →  FastAPI backend (main.py)  →  data.json
```

<details>
<summary>View project folder structure</summary>

```text
Anj_Challenge/
├── backend/
│   ├── main.py                # FastAPI app and all endpoints
│   ├── data.json              # Fictional medicine data
│   ├── requirements.txt       # Runtime dependencies
│   ├── requirements-dev.txt   # Runtime dependencies plus test tools
│   └── tests/
│       └── test_api.py        # API regression tests
├── frontend/
│   ├── index.html             # Page structure and forms
│   ├── script.js              # API calls, rendering and validation
│   └── style.css              # Layout and responsive styling
├── start.bat                  # Windows setup and run script
├── start.ps1                  # PowerShell setup and run script
├── start.sh                   # macOS/Linux setup and run script
└── README.md
```

</details>

### Notable Design Decisions

- **Stable IDs instead of names:** A name can be blank or duplicated, so it can't safely identify a record. IDs are UUIDs, so a deleted record's ID is never reused. The trade-off is less readable data, and a one-time change to the data file.
- **Name lookups still work:** `/update` and `/delete` accept a name as before, but return `409` if it matches more than one record rather than guessing.
- **Existing data is left alone:** New duplicate names are rejected, but existing duplicates are never merged or deleted. The blank name and missing price from the challenge data remain in `data.json`, and can now be updated or deleted by ID.
- **Keeping the JSON file:** A database would solve the file handling more completely, but the app's size doesn't justify it. A lock and atomic saves cover the realistic risks of a local app.
- **No frontend framework:** Plain JavaScript was enough for one page. The trade-off is that rendering is written by hand.

## Getting Started

### Prerequisites

- [Python 3](https://www.python.org/downloads/) (tested with 3.14)
- A modern web browser (tested with Microsoft Edge)

### 1. Clone

```bash
git clone https://github.com/Anj-13/Anj_Challenge.git
cd Anj_Challenge
```

### 2. Configure

No configuration is needed. The start scripts create a virtual environment in `backend/venv` and install the dependencies on first run.

### 3. Build and Run

**Windows (Command Prompt or PowerShell):**

```bash
.\start.bat
```

**Windows (PowerShell script):**

```powershell
.\start.ps1
```

**macOS/Linux:**

```bash
bash start.sh
```

To set up manually instead, run these from the repository root:

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Expected result:** The API runs at `http://127.0.0.1:8000`. Open `frontend/index.html` in your browser to use the app. Press `Ctrl+C` to stop the server.

## Usage

1. Start the backend, then open `frontend/index.html`. The medicine list and quarterly report load automatically.
2. Use the forms to add, update or delete a medicine, or use the Quick Update and Quick Delete buttons on a record.
3. Check the notification that appears, which shows whether the change succeeded and why it failed if it didn't.

Changes are saved to `backend/data.json`, so they remain after the server restarts. When the app adds IDs to records that don't have them, it first saves a copy of the file as `backend/data.json.bak`, which Git ignores.

## API Reference

`POST` and `DELETE` requests take form data, not JSON. Each of these six endpoints comes from the original app.

| Method | Endpoint | Fields | Description |
| --- | --- | --- | --- |
| `GET` | `/medicines` | None | Returns all medicines |
| `GET` | `/medicines/{name}` | None | Returns one medicine by exact name |
| `POST` | `/create` | `name`, `price` | Adds a medicine |
| `POST` | `/update` | `price`, and `id` or `name` | Updates a medicine's price |
| `DELETE` | `/delete` | `id` or `name` | Deletes a medicine |
| `GET` | `/average-price` | None | Returns the average of all valid prices |

If both `id` and `name` are sent, `id` is used. Names must be 3 to 50 characters, and prices must be finite numbers of 0 or more.

Errors return a matching status code and a `detail` message:

| Status | Meaning |
| --- | --- |
| `404` | The medicine was not found |
| `409` | The name is already in use on `/create`, or matches more than one medicine elsewhere |
| `422` | A submitted value is invalid, or neither `id` nor `name` was sent |
| `500` | The data file is missing or unreadable |

**Changes from the original API:**
- Records now include an `id`, and `/update` and `/delete` accept one.
- Failures now return the status codes above and a `detail` field, rather than `200` with an `error` field.
- `/create` and `/update` responses now include the saved record.
- `/average-price` now returns `200` with `average_price: null` when there are no valid prices.

## Testing & Quality

- **Automated tests:** 45 pytest tests cover all six endpoints, including invalid input, duplicates, missing prices, the ID migration, saving to file and damaged data files. They run against temporary files, so `data.json` is never touched.
- **How to run tests:**

  ```bash
  cd backend
  pip install -r requirements-dev.txt
  python -m pytest
  ```

- **Browser checks:** I tested the page in headless Microsoft Edge using a temporary data file. This covered every form and quick action, confirmation prompts, rejected requests, the server being offline, and layouts from 1280px down to 320px. These checks are not part of the repository.
- **Startup scripts:** `start.bat` and `start.ps1` were tested on Windows 10, and `start.sh` under Git Bash on Windows. This included first runs, repeat runs and missing Python. `start.sh` has not been run on macOS or Linux.
- **Validation:** The frontend checks input before sending it, and the API checks it again so that direct requests are held to the same rules.

## Challenges & Solutions

**From the review of my original submission:**

| Problem found | Fix | Result |
| --- | --- | --- |
| Rejected deletes followed the success path, because the frontend only checked for an `error` field | All requests now go through one function that checks the HTTP status | Success appears only after the API confirms a change |
| `showSuccessMessage` had been deleted, but nine calls to it remained, so no notification could ever appear | Added a new notification system and replaced every call | Users now see the outcome of every action |
| Missing prices appeared as `Price: $Not Available`, and a price of 0 would have been treated as missing | Added one `formatPrice` function that checks for a number | Prices display as `$0.00` or `Price: Not Available` |
| The API accepted negative prices | Added validation on `/create` and `/update` | Invalid prices return `422` and nothing is saved |
| Saving `price=nan` made `GET /medicines` return `500` on every request until the file was edited by hand | Rejected non-finite prices | The app can no longer be broken this way through the API |
| Update and delete acted on the first record with a matching name | Added stable IDs and ID-based dropdowns | Each action targets exactly one record, including duplicates and the unnamed record |
| `start.ps1` looked for `requirements.txt` in the wrong folder, and the scripts disagreed on where the virtual environment lived | Rewrote all three scripts | Each script installs and starts the app from any folder |
| The repository tracked `node_modules` for an Express dependency nothing used | Removed the dependency and updated `.gitignore` | The repository holds only the app, tests and scripts |

**From the original challenge:**

| Challenge | Approach | Outcome |
| --- | --- | --- |
| The API responded in Postman, but the list wouldn't load in the browser | Removed `host="0.0.0.0"` from `uvicorn.run` so the server used its default address | The list loaded on the page |
| Form submissions didn't match what the API expected | Read `main.py`, then sent the data with `FormData` | The forms send data the API accepts |

## Results & What I Learned

- **Outcome:** A working version of the original app, with reliable CRUD operations, validation on both sides, accurate error reporting and working setup instructions.
- **Skills gained:** HTTP status codes and API error design, server-side validation with FastAPI and Pydantic, stable identifiers, atomic file writes, regression testing with pytest, and writing cross-platform startup scripts.
- **Reflection:** Passing the happy path isn't the same as working. My original testing confirmed that things worked when used correctly, but never checked what happened when requests failed, which is where most of these bugs were. A frontend check can't replace validation on the server either, because the API can be called directly.

## Future Improvements

- [ ] Allow records to be renamed, so the unnamed record can be given a name.
- [ ] Add search and filtering to the medicine list.
- [ ] Make the API address configurable so the app can be deployed.
- [ ] Add browser tests to the repository, and run all tests automatically on each push.
- [ ] Pin dependency versions so setups are reproducible.
- [ ] Run `start.sh` on macOS and Linux.
- [ ] Move to a database if the app ever needs more than one user.

## Contributors

Developed by [Anj-13](https://github.com/Anj-13). The core API and sample data come from the [challenge starter repository](https://github.com/SamThompson95/lilly-recruitment-challenge).

## License

No license has been specified.
