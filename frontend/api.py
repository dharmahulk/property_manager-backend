
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
index_template = Jinja2Templates(directory="frontend/BootStraps/startbootstrap/dist")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
   return index_template.TemplateResponse("index.html", {"request": request})