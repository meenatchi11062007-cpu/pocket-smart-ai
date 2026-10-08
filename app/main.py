import json
from pathlib import Path
from fastapi import FastAPI,Request,Depends,Form,UploadFile,File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .config import settings,UPLOAD_DIR
from .database import Base,engine,get_db
from .models import User,Recommendation
from .auth import hash_password,verify_password,create_access_token,current_user,require_user
from .schemas import HomeRequest,PartyRequest,JewelryRequest
from .ai.gemini_utils import generate
from .services.recommendation_service import save,history
Base.metadata.create_all(bind=engine)
app=FastAPI(title=settings.APP_NAME)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.mount('/static', StaticFiles(directory=str(Path(__file__).resolve().parent / 'static')), name='static')
app.mount('/uploads', StaticFiles(directory=str(UPLOAD_DIR)), name='uploads')
templates=Jinja2Templates(directory=str(Path(__file__).resolve().parent / 'templates'))
def page(request,name,ctx=None):
    ctx=ctx or {}; db=next(get_db());
    try: ctx.update({'request':request,'user':current_user(request,db)}); return templates.TemplateResponse(request=request,name=name,context=ctx)
    finally: db.close()
def show(request,r,user=None):
    x=json.loads(r.result_json); x.update({'recommendation_id':r.id,'planner_type':r.planner_type}); return templates.TemplateResponse(request=request,name='recommendations.html',context={'request':request,'user':user,'result':x})
@app.get('/')
def home(request:Request): return page(request,'home.html')
@app.get('/register')
def reg_page(request:Request): return page(request,'register.html')
@app.post('/register')
def reg(name:str=Form(...),email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    email=email.strip().lower()
    if len(password)<6:return RedirectResponse('/register?error=Password%20must%20be%20at%20least%206%20characters',303)
    if db.query(User).filter(User.email==email).first():return RedirectResponse('/register?error=Email%20already%20registered',303)
    u=User(name=name.strip(),email=email,password_hash=hash_password(password));db.add(u);db.commit();db.refresh(u); r=RedirectResponse('/dashboard',303);r.set_cookie('access_token',create_access_token(u.id),httponly=True,samesite='lax',max_age=86400);return r
@app.get('/login')
def login_page(request:Request):return page(request,'login.html')
@app.post('/login')
def login(email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==email.strip().lower()).first()
    if not u or not verify_password(password,u.password_hash):return RedirectResponse('/login?error=Invalid%20email%20or%20password',303)
    r=RedirectResponse('/dashboard',303);r.set_cookie('access_token',create_access_token(u.id),httponly=True,samesite='lax',max_age=86400);return r
@app.get('/logout')
def logout():r=RedirectResponse('/',303);r.delete_cookie('access_token');return r
@app.post('/token')
def token(email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==email.strip().lower()).first()
    if not u or not verify_password(password,u.password_hash):raise HTTPException(401,'Invalid credentials')
    return {'access_token':create_access_token(u.id),'token_type':'bearer'}
@app.get('/session-info')
def session_info(request:Request,db:Session=Depends(get_db)):
    u=current_user(request,db);return {'logged_in':bool(u),'user_id':u.id if u else None,'name':u.name if u else None}
@app.get('/session-data')
def session_data(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db);h=history(db,u.id);return {'user_id':u.id,'recommendation_count':len(h),'recent_planners':[x.planner_type for x in h[:5]]}
@app.get('/dashboard')
def dashboard(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db);return templates.TemplateResponse(request=request,name='dashboard.html',context={'request':request,'user':u,'history':history(db,u.id)})
@app.get('/planner/{kind}')
def planner(kind:str,request:Request,db:Session=Depends(get_db)):
    if kind not in ('home','party','jewelry'): raise HTTPException(404, 'Planner not found')
    u=require_user(request, db)
    return templates.TemplateResponse(request=request, name=f'planner_{kind}.html', context={'request':request,'user':u})
@app.post('/generate-home')
def gen_home(request:Request,budget:float=Form(...),room_type:str=Form(...),style:str=Form(...),items:str=Form(...),location:str=Form('India'),db:Session=Depends(get_db)):
    u=require_user(request,db);d=HomeRequest(budget=budget,room_type=room_type,style=style,items=items,location=location).model_dump();r=save(db,u.id,'home',budget,d,generate('home',d));return show(request,r,u)
@app.post('/generate-party')
def gen_party(request:Request,budget:float=Form(...),guests:int=Form(...),event_type:str=Form(...),venue:str=Form(...),city:str=Form('Chennai'),db:Session=Depends(get_db)):
    u=require_user(request,db);d=PartyRequest(budget=budget,guests=guests,event_type=event_type,venue=venue,city=city).model_dump();r=save(db,u.id,'party',budget,d,generate('party',d));return show(request,r,u)
@app.post('/generate-jewelry')
async def gen_jewelry(request:Request,budget:float=Form(...),occasion:str=Form(...),style:str=Form(...),outfit_notes:str=Form(''),outfit_image:UploadFile|None=File(None),db:Session=Depends(get_db)):
    u=require_user(request,db);d=JewelryRequest(budget=budget,occasion=occasion,style=style,outfit_notes=outfit_notes).model_dump();path=None
    if outfit_image and outfit_image.filename:
        if outfit_image.content_type not in {'image/jpeg','image/png','image/webp'}:raise HTTPException(400,'Only JPG, PNG or WEBP images are supported.')
        content=await outfit_image.read()
        if len(content)>settings.MAX_UPLOAD_MB*1024*1024:raise HTTPException(400,'Image is too large.')
        path=str(UPLOAD_DIR/f'user_{u.id}_outfit{Path(outfit_image.filename).suffix.lower()}');Path(path).write_bytes(content)
    r=save(db,u.id,'jewelry',budget,d,generate('jewelry',d,path));return show(request,r,u)
@app.get('/recommendations-details/{rid}')
def details(rid:int,request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db);r=db.get(Recommendation,rid)
    if not r or r.user_id!=u.id:raise HTTPException(404,'Recommendation not found')
    return show(request,r,u)
@app.get('/history')
def hist(request:Request,db:Session=Depends(get_db)):
    u=require_user(request,db);return templates.TemplateResponse(request=request,name='history.html',context={'request':request,'user':u,'history':history(db,u.id)})
@app.get('/startup')
def startup():return {'status':'ready','app':settings.APP_NAME}
@app.get('/health')
def health():return {'status':'ok'}
