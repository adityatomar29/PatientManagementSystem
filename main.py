from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse # Response to client 
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

# First Endpoint
app = FastAPI() # Object of FastAPI


# Creating Pydantic model for create endpoint
class Patient(BaseModel):
    # Add fields based on data in JSON file 
    id: Annotated[str, Field(...,description='ID of the patient', examples=['P001'])]
    name : Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where patient is living')]
    age: Annotated[int, Field(...,gt=0, lt=120, description='Age of patient')] 
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of patient')]
    height: Annotated[float, Field(..., gt=0, description='Height of the patient in Mtr')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the patient in Kgs')]

    # Making computed field 
    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2), 2)
        return bmi 
    

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi <25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
        

# Creating Pydantic model for update endpoint 
class PatientUpdate(BaseModel):
    # 'id' we are asking as path parameter so we do not include it in request body
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
        


# Creating helper function to load and save data from json file 
def load_data():
    with open('patients.json', 'r') as f:
        data = json.load(f)

    return data

def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data, f)


@app.get("/") # Creating Route, Getting request from server
def hello():
    return{"message": "Patient Management System API"}

# Making another route url (endpoint)
@app.get("/about")
def about():
    return{"message":"A fully functional API to manage your patient records"}


@app.get("/view")
def view():
    content = load_data()

    return content

# Path parameters 
@app.get('/patient/{patient_id}')
def view_patient(patient_id: str):
    # Load all the patients 
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail='Patient not found.')

# Query Parameter 
@app.get('/sort')
def sort_patients(sort_by:str = Query(...,description='Sort on the basis of height, weight or anything'), order:str= Query('asc', description='Sort in ascending or descending order (by default it is ascending)')):

    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail = f'Invalid field select from {valid_fields}')
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='Invalid order select between asc and desc')
    data = load_data()

    sort_order = True if order=='desc' else False

    sorted_data = sorted(data.values(), key = lambda x: x.get(sort_by, 0), reverse=sort_order)

    return sorted_data


@app.post('/create')
def create_patient(patient: Patient):
    # Load existing data 
    data = load_data()

    # Check if patient already exist
    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient already exists')

    # new patient add (ConvertPydantic object into dictionary to add)
    data[patient.id] = patient.model_dump(exclude=['id'])

    # Save into JSON file 
    save_data(data)

    return JSONResponse(status_code=201, content={'message': 'Patient created successfully'})



# Update endpoint 
@app.put('/edit/{patient_id}')
def update_patient(patient_id:str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id]
    # Convert object in dictionary 
    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    # existing_patient_info_ -> Make new pydantic object for computed fields -> convert to dictionary again 

    existing_patient_info['id'] = patient_id # Because Patient object expects id as parameter so below code will give error without this
    patient_pydantic_object = PatientUpdate(**updated_patient_info)

    existing_patient_info = patient_pydantic_object.model_dump(exclude='id') # Object -> dictionary

    data[patient_id] = existing_patient_info # Add this to data

    # save the data 
    save_data(data)

    return JSONResponse(status_code=200, content={"message":"Patient updated"})


# Delete endpoint
@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={'message':'Patient deleted'})


