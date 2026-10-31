"""
This module defines a FastAPI application for managing a list of medicines.
Medicines are stored in data.json and each record has a stable id, because
names are not guaranteed to be unique or even present in the existing data.
Endpoints:
- GET /medicines: Retrieve all medicines.
- GET /medicines/{name}: Retrieve a single medicine by name.
- POST /create: Create a new medicine with a specified name and price.
- POST /update: Update the price of a medicine, selected by id or name.
- DELETE /delete: Delete a medicine, selected by id or name.
- GET /average-price: Report the average of all valid prices.
Errors are returned with a matching HTTP status and a "detail" message:
- 404: The medicine was not found.
- 409: The name is already in use, or matches more than one medicine.
- 422: The submitted values are invalid.
- 500: The data file is missing or unreadable.
Usage:
Run this module directly to start the FastAPI application.
"""
import json
import math
import os
import shutil
import threading
import uuid
from pathlib import Path
from typing import Annotated, Optional

import uvicorn
from fastapi import FastAPI, Form, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import StringConstraints

# Resolved from this file so the server can be started from any folder
DATA_FILE = Path(os.environ.get("MEDICINE_DATA_FILE", Path(__file__).with_name("data.json")))

MedicineName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50), Form()]
MedicinePrice = Annotated[float, Form(ge=0, allow_inf_nan=False)]

FIELD_ERRORS = {
    "name": "Name must be between 3 and 50 characters.",
    "price": "Price must be a number of 0 or more.",
}

# FastAPI runs these endpoints in a thread pool, so each read-then-write has to hold this lock
db_lock = threading.Lock()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
def validation_error(request, exc):
    """
    This function replaces FastAPI's default validation response with a readable message.
    Args:
        request (Request): The request that failed validation.
        exc (RequestValidationError): The validation errors.
    Returns:
        JSONResponse: A 422 response naming each invalid field once.
    """
    fields = dict.fromkeys(error["loc"][-1] for error in exc.errors())
    detail = " ".join(FIELD_ERRORS.get(field, f"{field} is invalid.") for field in fields)
    return JSONResponse(status_code=422, content={"detail": detail})

def save_db(db):
    """
    This function writes the database to a temporary file and then swaps it into place,
    so a failed write cannot leave data.json half written.
    Args:
        db (dict): The database to save.
    """
    temp_file = DATA_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as meds:
        json.dump(db, meds, indent=4)
    os.replace(temp_file, DATA_FILE)

def load_db():
    """
    This function reads the data file. Records without an id are given one and saved,
    after backing up the original file once. No other values are changed.
    Returns:
        dict: The database, with an id on every medicine.
    """
    try:
        with open(DATA_FILE, encoding="utf-8") as meds:
            db = json.load(meds)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="The data file could not be found.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="The data file is not valid JSON.")

    if not isinstance(db, dict) or not isinstance(db.get("medicines"), list):
        raise HTTPException(status_code=500, detail="The data file has no medicines list.")

    missing_ids = [med for med in db["medicines"] if "id" not in med]
    if missing_ids:
        backup_file = DATA_FILE.with_suffix(".json.bak")
        if not backup_file.exists():
            shutil.copy2(DATA_FILE, backup_file)
        for med in missing_ids:
            med["id"] = str(uuid.uuid4())
        save_db(db)

    return db

def find_medicine(db, med_id=None, name=None):
    """
    This function finds exactly one medicine, preferring the id over the name.
    Args:
        db (dict): The database to search.
        med_id (str): The id of the medicine.
        name (str): The name of the medicine.
    Returns:
        dict: The matching medicine.
    Raises:
        HTTPException: 422 if neither value is given, 404 if nothing matches,
        or 409 if the name matches more than one medicine.
    """
    if med_id:
        matches = [med for med in db["medicines"] if med["id"] == med_id]
    elif name and name.strip():
        name = name.strip()
        matches = [med for med in db["medicines"] if med.get("name") == name]
    else:
        raise HTTPException(status_code=422, detail="Please provide a medicine id or name.")

    if not matches:
        raise HTTPException(status_code=404, detail="Medicine not found")
    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail=f"{len(matches)} medicines are named {name}. Please use the id instead.",
        )
    return matches[0]

def is_valid_price(price):
    """
    This function checks whether a stored price can be used in calculations.
    Args:
        price: The stored value, which may be missing or invalid in existing data.
    Returns:
        bool: True for a finite, non-negative number.
    """
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return False
    return math.isfinite(price) and price >= 0

@app.get("/medicines")
def get_all_meds():
    """
    This function reads the data.json file and returns all medicines.
    Returns:
        dict: A dictionary of all medicines
    """
    with db_lock:
        return load_db()

@app.get("/medicines/{name}")
def get_single_med(name: str):
    """
    This function reads the data.json file and returns a single medicine by name.
    Args:
        name (str): The name of the medicine to retrieve.
    Returns:
        dict: A dictionary containing the medicine details
    """
    with db_lock:
        return find_medicine(load_db(), name=name)

@app.post("/create")
def create_med(name: MedicineName, price: MedicinePrice):
    """
    This function creates a new medicine with the specified name and price.
    It expects the name and price to be provided as form data.
    Args:
        name (str): The name of the medicine.
        price (float): The price of the medicine.
    Returns:
        dict: A message confirming the medicine was created successfully, and the new record.
    """
    with db_lock:
        current_db = load_db()
        for med in current_db["medicines"]:
            if str(med.get("name", "")).lower() == name.lower():
                raise HTTPException(status_code=409, detail=f"A medicine named {med['name']} already exists.")

        new_med = {"name": name, "price": price, "id": str(uuid.uuid4())}
        current_db["medicines"].append(new_med)
        save_db(current_db)

    return {"message": f"Medicine created successfully with name: {name}", "medicine": new_med}

@app.post("/update")
def update_med(
    price: MedicinePrice,
    med_id: Optional[str] = Form(None, alias="id"),
    name: Optional[str] = Form(None),
):
    """
    This function updates the price of a medicine selected by id or name.
    It expects the values to be provided as form data.
    Args:
        price (float): The new price of the medicine.
        med_id (str): The id of the medicine, sent as "id".
        name (str): The name of the medicine, used when no id is given.
    Returns:
        dict: A message confirming the medicine was updated successfully, and the updated record.
    """
    with db_lock:
        current_db = load_db()
        med = find_medicine(current_db, med_id, name)
        med["price"] = price
        save_db(current_db)

    return {"message": f"Medicine updated successfully with name: {med.get('name') or 'Unknown Med'}", "medicine": med}

@app.delete("/delete")
def delete_med(med_id: Optional[str] = Form(None, alias="id"), name: Optional[str] = Form(None)):
    """
    This function deletes a medicine selected by id or name.
    It expects the values to be provided as form data.
    Args:
        med_id (str): The id of the medicine, sent as "id".
        name (str): The name of the medicine, used when no id is given.
    Returns:
        dict: A message confirming the medicine was deleted successfully.
    """
    with db_lock:
        current_db = load_db()
        med = find_medicine(current_db, med_id, name)
        current_db["medicines"].remove(med)
        save_db(current_db)

    return {"message": f"Medicine deleted successfully with name: {med.get('name') or 'Unknown Med'}"}

@app.get("/average-price")
def get_average_price():
    """
    This function reports the average of all valid prices. Missing, non-numeric
    and negative prices are left out of the calculation.
    Returns:
        dict: The average, which is None when there are no valid prices, and the counts behind it.
    """
    with db_lock:
        medicines = load_db()["medicines"]

    valid_prices = [med.get("price") for med in medicines if is_valid_price(med.get("price"))]

    if not valid_prices:
        return {
            "average_price": None,
            "total_medicines": len(medicines),
            "medicines_with_valid_prices": 0,
            "message": "No valid prices found",
        }

    average_price = round(sum(valid_prices) / len(valid_prices), 2)
    return {
        "average_price": average_price,
        "total_medicines": len(medicines),
        "medicines_with_valid_prices": len(valid_prices),
        "message": f"Average price of {len(valid_prices)} medicines: ${average_price}",
    }

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
