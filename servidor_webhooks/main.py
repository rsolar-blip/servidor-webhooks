from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "msg": "servidor listo para webhooks"}