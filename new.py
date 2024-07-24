from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI()

# Load data from a JSON file
def load_json(filename):
    with open(filename,'r',encoding='utf-8') as file:
        return json.load(file)

# Load the JSON data
data = load_json('address/countries.json')


class Country(BaseModel):
    id: int
    name: str

class State(BaseModel):
    id: int
    name: str
    

@app.get("/countries")
def get_countries():
    return {'status': 200, 'data': [{"id": country["id"], "name": country["name"]} for country in data], 'message': 'Success'}

@app.get("/countries/{country_id}/states")
def get_states(country_id: int):
    for country in data:
        if country["id"] == country_id:
            if "states" in country:
                return {'status': 200, 'data': [{"id": state["id"], "name": state["name"]} for state in country["states"]], 'message': 'Success'}
            else:
                return {'status': 404, 'data': [], 'message': 'No states found for this country'}
    raise HTTPException(status_code=404, detail="Country not found")

