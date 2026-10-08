from pydantic import BaseModel,Field
class HomeRequest(BaseModel):
    budget:float=Field(gt=0); room_type:str=Field(min_length=2,max_length=50); style:str=Field(min_length=2,max_length=80); items:str=Field(min_length=2,max_length=500); location:str='India'
class PartyRequest(BaseModel):
    budget:float=Field(gt=0); guests:int=Field(gt=0,le=10000); event_type:str=Field(min_length=2,max_length=80); venue:str=Field(min_length=2,max_length=200); city:str='Chennai'
class JewelryRequest(BaseModel):
    budget:float=Field(gt=0); occasion:str=Field(min_length=2,max_length=80); style:str=Field(min_length=2,max_length=100); outfit_notes:str=''
