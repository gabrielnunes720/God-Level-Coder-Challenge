# Arquivo: conexao_db.py
import psycopg2.pool
import sys

# O pool agora começa como None
connection_pool = None

# --- CONFIGURAÇÕES ---
db_config = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': '1234',
    'port': 5432
}
# ---------------------------

def init_pool():
    """Cria o pool de conexões. Deve ser chamada na inicialização da API."""
    global connection_pool
    if connection_pool is None:
        try:
            print("Tentando criar pool de conexões...")
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,
                20,
                **db_config
            )
            print("Pool de conexões criado com sucesso.")
        except Exception as e:
            print(f"--- ERRO FATAL AO CRIAR POOL: {e}", file=sys.stderr)
            sys.exit(1) # Sai da aplicação se o banco falhar

def get_connection():
    """Pega uma conexão do pool."""
    global connection_pool
    if connection_pool is None:
        print("ERRO: Pool não foi inicializado. Chame init_pool() primeiro.", file=sys.stderr)
        return None
        
    try:
        conn = connection_pool.getconn()
        return conn
    except Exception as e:
        print(f"Erro ao pegar conexão do pool: {e}", file=sys.stderr)
        return None

def release_connection(conn):
    """Devolve uma conexão ao pool."""
    if connection_pool:
        connection_pool.putconn(conn)