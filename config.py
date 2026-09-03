"""
Configurações Globais do RPG de Mushoku Tensei.
Carrega variáveis de ambiente de forma segura utilizando python-dotenv.
"""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent

# Configuração do Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Caminhos de Armazenamento e Conteúdo
DATABASE_DIR = BASE_DIR / os.getenv("DATABASE_DIR", "database/data")
PLAYERS_DIR = DATABASE_DIR / "players"
CONTENT_DIR = BASE_DIR / "content"
DATA_DIR = CONTENT_DIR / "data"
TEXTS_DIR = CONTENT_DIR / "texts"
IMAGES_DIR = CONTENT_DIR / "images"

# Garante que as pastas básicas existam
os.makedirs(PLAYERS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEXTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Constantes do Universo de Mushoku Tensei
RANKS_AVENTUREIRO = ["F", "E", "D", "C", "B", "A", "S"]
RANKS_MAGIA = ["Iniciante", "Intermediário", "Avançado", "Santo", "Rei", "Imperial", "Divino"]
ESTILOS_ESPADA = ["Deus da Espada", "Deus da Água", "Deus do Norte"]
CONTINENTES = {
    "central": "Continente Central (Reino de Asura / Sharia)",
    "demon": "Continente Demônio (Rikarisu)",
    "milis": "Continente Sagrado de Milis (Milishion)",
    "begaritt": "Continente de Begaritt (Labirintos e Deserto)"
}
