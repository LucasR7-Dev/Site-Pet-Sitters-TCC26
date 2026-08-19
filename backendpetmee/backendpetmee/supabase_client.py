import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError('SUPABASE_URL e SUPABASE_ANON_KEY devem estar configuradas no arquivo .env')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
