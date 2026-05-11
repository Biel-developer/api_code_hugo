from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, init_db, JogoDB

app = FastAPI(title="API Biblioteca de Jogos", docs_url=None, redoc_url=None, openapi_url=None)

FIXED_TOKEN = "550e8400-e29b-41d4-a716-446655440000"

VALID_EMAIL = "usuario@esoft.com"
VALID_PASSWORD = "Abc123"

class LoginRequest(BaseModel):
    email: str
    password: str

class JogoCreate(BaseModel):
    nome: str
    tipo: str
    nota: float
    review: str

class JogoUpdate(BaseModel):
    nome: str
    tipo: str
    nota: float
    review: str

class JogoResponse(BaseModel):
    id: int
    nome: str
    tipo: str
    nota: float
    review: str

    class Config:
        from_attributes = True

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Libera apenas o endpoint de login e a documentação
    open_paths = {"/login", "/"}
    if request.url.path in open_paths:
        return await call_next(request)

    token = request.headers.get("Authorization")
    if not token or token != FIXED_TOKEN:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Não autorizado. Faça login primeiro."})

    return await call_next(request)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def home():
    return {"status": "API ONLINE"}

@app.post("/login", status_code=200)
def login(body: LoginRequest):
    if body.email == VALID_EMAIL and body.password == VALID_PASSWORD:
        return {"token": FIXED_TOKEN}
    raise HTTPException(status_code=401, detail="Credenciais inválidas.")

@app.get("/jogos", response_model=list[JogoResponse], status_code=200)
def listar_jogos(db: Session = Depends(get_db)):
    return db.query(JogoDB).all()

@app.get("/jogos/{id}", response_model=JogoResponse, status_code=200)
def buscar_jogo(id: int, db: Session = Depends(get_db)):
    jogo = db.query(JogoDB).filter(JogoDB.id == id).first()
    if not jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")
    return jogo

@app.post("/jogos", response_model=JogoResponse, status_code=201)
def criar_jogo(body: JogoCreate, db: Session = Depends(get_db)):
    jogo = JogoDB(**body.model_dump())
    db.add(jogo)
    db.commit()
    db.refresh(jogo)
    return jogo

@app.put("/jogos/{id}", response_model=JogoResponse, status_code=200)
def atualizar_jogo(id: int, body: JogoUpdate, db: Session = Depends(get_db)):
    jogo = db.query(JogoDB).filter(JogoDB.id == id).first()
    if not jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")
    for campo, valor in body.model_dump().items():
        setattr(jogo, campo, valor)
    db.commit()
    db.refresh(jogo)
    return jogo

@app.delete("/jogos/{id}", status_code=204)
def deletar_jogo(id: int, db: Session = Depends(get_db)):
    jogo = db.query(JogoDB).filter(JogoDB.id == id).first()
    if not jogo:
        raise HTTPException(status_code=404, detail="Jogo não encontrado.")
    db.delete(jogo)
    db.commit()
    return Response(status_code=204)