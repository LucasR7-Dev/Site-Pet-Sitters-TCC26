import os
from supabase import create_client, Client

# Busca a URL e a KEY do arquivo .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_ANON_KEY:
    raise ValueError('A variavel SUPABASE_ANON_KEY não foi configurada no arquivo .env')


# Cria a instância da conexão do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)