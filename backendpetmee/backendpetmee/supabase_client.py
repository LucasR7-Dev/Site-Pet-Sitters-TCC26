import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

<<<<<<< HEAD

# Busca a URL e a KEY do arquivo .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_ANON_KEY:
    raise ValueError('A variavel SUPABASE_ANON_KEY não foi configurada no arquivo .env')


# Cria a instância da conexão do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

#definindo caminho .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
=======
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client | None = (
    create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if SUPABASE_URL and SUPABASE_ANON_KEY
    else None
)


def get_supabase() -> Client:
    """Retorna o cliente configurado e deixa o erro claro quando falta configuração."""
    if supabase is None:
        raise RuntimeError(
            'Configure SUPABASE_URL e SUPABASE_ANON_KEY nas variáveis do ambiente.'
        )
    return supabase
>>>>>>> efea9b9 (Crie a pagina loja no projeto, e a aba petshops foi feita e a pagina cuidadores também, tem alguns erros de design mas pode ser modificado mais tarde)
