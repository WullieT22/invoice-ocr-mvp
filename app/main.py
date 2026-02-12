from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from services.extractor import extract_invoice_data
from services.matcher import match_invoice

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_invoices(request: Request, files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        invoice_data = await extract_invoice_data(file)
        match_result = match_invoice(invoice_data)
        results.append({
            "filename": file.filename,
            "data": invoice_data,
            "match": match_result
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "results": results
    })
