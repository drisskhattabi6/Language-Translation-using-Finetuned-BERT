from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import torch
from transformers import AutoTokenizer, EncoderDecoderModel


from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")


# -------------------------
# Load model + tokenizer
# -------------------------
MODEL_NAME = "idrisskh/bert-encdec-eng-ara"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)
model = EncoderDecoderModel.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Fix special tokens
model.config.decoder_start_token_id = tokenizer.cls_token_id or tokenizer.bos_token_id or 101
model.config.eos_token_id = tokenizer.sep_token_id or tokenizer.eos_token_id or 102
model.config.pad_token_id = tokenizer.pad_token_id or 0

# -------------------------
# FastAPI setup
# -------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# Translation function
# -------------------------
def translate(sentence, max_len=64):
    inputs = tokenizer(sentence, return_tensors="pt", truncation=True, padding=True).to(device)
    outputs = model.generate(
        **inputs,
        max_length=max_len,
        num_beams=5,
        early_stopping=True,
        decoder_start_token_id=model.config.decoder_start_token_id,
        eos_token_id=model.config.eos_token_id,
        pad_token_id=model.config.pad_token_id
    )
    pred = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return pred.strip()

# -------------------------
# Routes
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "translation": ""})

@app.post("/translate", response_class=HTMLResponse)
async def translate_text(request: Request, english_text: str = Form(...)):
    arabic_translation = translate(english_text)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "translation": arabic_translation, "english_text": english_text}
    )
