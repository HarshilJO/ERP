from typing import List, Optional
from pydantic import BaseModel


class countries(BaseModel):
    id:int
    name:str