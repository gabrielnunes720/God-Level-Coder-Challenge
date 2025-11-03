from flask import Flask, jsonify, request
from conexao_db import init_pool, get_connection, release_connection
import sys
from flask_cors import CORS
from datetime import datetime, timedelta

# Cria a aplicação Flask
app = Flask(__name__)
CORS(app) 

# Inicializa o Pool de Conexões do banco de dados
init_pool()

@app.route('/')
def home():
    """Página inicial apenas para teste."""
    return "O servidor da API está rodando!"

# --- ENDPOINT DE ANÁLISE TOP PRODUTOS (Painel Resumo) ---
@app.route('/api/analise/top-produtos')
def analisar_top_produtos_atualizado():
    print("Recebida requisição em /api/analise/top-produtos")
    conn = None
    try:
        # --- 1. Coletar Filtros ---
        lojas_selecionadas = request.args.getlist('loja')
        canais_selecionados = request.args.getlist('canal')
        dia_semana = request.args.get('dia_semana', default=None, type=int)
        hora_inicio = request.args.get('hora_inicio', default=0, type=int)
        hora_fim = request.args.get('hora_fim', default=23, type=int)
        ordenacao = request.args.get('ordenacao', default='DESC').upper()
        limite = request.args.get('limite', default=10, type=int)

        if ordenacao not in ('ASC', 'DESC'):
            ordenacao = 'DESC'

        # --- 2. Montar Query ---
        params = []
        where_clauses = []

        where_clauses.append("EXTRACT(HOUR FROM s.created_at) BETWEEN %s AND %s")
        params.extend([hora_inicio, hora_fim])

        if dia_semana is not None:
            where_clauses.append("EXTRACT(ISODOW FROM s.created_at) = %s")
            params.append(dia_semana)
        if lojas_selecionadas:
            where_clauses.append("sb.name IN %s") 
            params.append(tuple(lojas_selecionadas))
        if canais_selecionados:
            where_clauses.append("c.name IN %s")
            params.append(tuple(canais_selecionados))

        sql_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        sql_query = f"""
            SELECT p.name, sb.name, c.name, SUM(ps.quantity) AS total_vendido
            FROM product_sales ps
            JOIN sales s ON ps.sale_id = s.id
            JOIN products p ON ps.product_id = p.id
            JOIN channels c ON s.channel_id = c.id
            JOIN stores l ON s.store_id = l.id 
            JOIN sub_brands sb ON l.sub_brand_id = sb.id 
            {sql_where}
            GROUP BY p.name, sb.name, c.name   
            ORDER BY total_vendido {ordenacao} 
            LIMIT %s;
        """
        params.append(limite)

        # --- 3. Executar ---
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_query, tuple(params))
            produtos = cursor.fetchall()
            resultado_formatado = [
                {"produto": nome, "loja": loja, "canal": canal, "vendas": float(total)} 
                for nome, loja, canal, total in produtos
            ]
            return jsonify(resultado_formatado)

    except Exception as e:
        print(f"ERRO [top-produtos]: {e}", file=sys.stderr)
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn: release_connection(conn)

# --- ENDPOINT DE KPIS (Painel Resumo) ---
@app.route('/api/analise/resumo-kpis')
def analisar_resumo_kpis():
    print("Recebida requisição em /api/analise/resumo-kpis")
    conn = None
    try:
        # --- 1. Coletar Filtros ---
        lojas_selecionadas = request.args.getlist('loja')
        canais_selecionados = request.args.getlist('canal')
        dia_semana = request.args.get('dia_semana', default=None, type=int)
        hora_inicio = request.args.get('hora_inicio', default=0, type=int)
        hora_fim = request.args.get('hora_fim', default=23, type=int)

        # --- 2. Montar Filtros Base ---
        # (Estes filtros serão usados em AMBAS as queries)
        base_params = []
        base_where_clauses = []

        base_where_clauses.append("EXTRACT(HOUR FROM s.created_at) BETWEEN %s AND %s")
        base_params.extend([hora_inicio, hora_fim])

        if dia_semana is not None:
            base_where_clauses.append("EXTRACT(ISODOW FROM s.created_at) = %s")
            base_params.append(dia_semana)
        if lojas_selecionadas:
            base_where_clauses.append("sb.name IN %s")
            base_params.append(tuple(lojas_selecionadas))
        if canais_selecionados:
            base_where_clauses.append("c.name IN %s")
            base_params.append(tuple(canais_selecionados))

        # --- 3. Query de KPIs (Concluídos) ---
        params_kpis = base_params.copy()
        where_kpis = " AND ".join(base_where_clauses + ["s.sale_status_desc = 'COMPLETED'"])
        
        sql_query_kpis = f"""
            SELECT
                COUNT(s.id) AS pedidos_concluidos,
                SUM(s.value_paid) AS faturamento_total,
                AVG(s.value_paid) AS ticket_medio,
                COUNT(DISTINCT s.customer_id) AS clientes_unicos
            FROM sales s
            JOIN channels c ON s.channel_id = c.id
            JOIN stores l ON s.store_id = l.id
            JOIN sub_brands sb ON l.sub_brand_id = sb.id
            WHERE {where_kpis};
        """
        
        # --- 4. Query de Cancelados ---
        params_cancelados = base_params.copy()
        where_cancelados = " AND ".join(base_where_clauses + ["s.sale_status_desc = 'CANCELLED'"])

        sql_query_cancelados = f"""
            SELECT COUNT(s.id) AS pedidos_cancelados
            FROM sales s
            JOIN channels c ON s.channel_id = c.id
            JOIN stores l ON s.store_id = l.id
            JOIN sub_brands sb ON l.sub_brand_id = sb.id
            WHERE {where_cancelados};
        """

        # --- 5. Executar ---
        conn = get_connection()
        kpis = {}
        with conn.cursor() as cursor:
            cursor.execute(sql_query_kpis, tuple(params_kpis))
            res_kpis = cursor.fetchone()
            
            cursor.execute(sql_query_cancelados, tuple(params_cancelados))
            res_cancelados = cursor.fetchone()

            # --- 6. Formatar Resultado ---
            pedidos_concluidos = float(res_kpis[0] or 0)
            faturamento_total = float(res_kpis[1] or 0)
            ticket_medio = float(res_kpis[2] or 0)
            clientes_unicos = float(res_kpis[3] or 0)
            pedidos_cancelados = float(res_cancelados[0] or 0)
            total_pedidos = pedidos_concluidos + pedidos_cancelados

            kpis = {
                "faturamento_total": faturamento_total,
                "pedidos_concluidos": pedidos_concluidos,
                "ticket_medio": ticket_medio,
                "pedidos_cancelados": pedidos_cancelados,
                "taxa_cancelamento": (pedidos_cancelados / total_pedidos) if total_pedidos > 0 else 0,
                "clientes_unicos": clientes_unicos,
                "frequencia_cliente": (pedidos_concluidos / clientes_unicos) if clientes_unicos > 0 else 0,
                "gasto_medio_cliente": (faturamento_total / clientes_unicos) if clientes_unicos > 0 else 0
            }
            return jsonify(kpis)

    except Exception as e:
        print(f"ERRO [resumo-kpis]: {e}", file=sys.stderr)
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn: release_connection(conn)


# --- FUNÇÃO AUXILIAR PARA FILTROS DE GRÁFICOS ---
def get_base_filters():
    """Coleta filtros comuns para os endpoints de gráficos."""
    lojas_selecionadas = request.args.getlist('loja')
    canais_selecionados = request.args.getlist('canal')
    dia_semana = request.args.get('dia_semana', default=None, type=int)
    
    # Período fixo de 30 dias para gráficos de tendência
    dias_atras = request.args.get('dias', default=30, type=int)
    data_inicio = datetime.now() - timedelta(days=dias_atras)

    params = [data_inicio]
    where_clauses = ["s.created_at >= %s"]

    if dia_semana is not None:
        where_clauses.append("EXTRACT(ISODOW FROM s.created_at) = %s")
        params.append(dia_semana)
    if lojas_selecionadas:
        where_clauses.append("sb.name IN %s")
        params.append(tuple(lojas_selecionadas))
    if canais_selecionados:
        where_clauses.append("c.name IN %s")
        params.append(tuple(canais_selecionados))
        
    # SQL Joins necessários para estes filtros
    sql_joins = """
        JOIN stores l ON s.store_id = l.id
        JOIN sub_brands sb ON l.sub_brand_id = sb.id
        JOIN channels c ON s.channel_id = c.id
    """
    
    return params, where_clauses, sql_joins

# --- ENDPOINT GRÁFICO 1: Vendas por Dia (Linha) ---
@app.route('/api/graficos/vendas-por-dia-loja')
def grafico_vendas_por_dia_loja():
    print("Recebida requisição em /api/graficos/vendas-por-dia-loja")
    conn = None
    try:
        params, where_clauses, sql_joins = get_base_filters()
        where_clauses.append("s.sale_status_desc = 'COMPLETED'") # Apenas vendas concluídas
        sql_where = "WHERE " + " AND ".join(where_clauses)

        sql_query = f"""
            SELECT DATE(s.created_at) AS dia, sb.name AS loja, SUM(s.value_paid) AS faturamento
            FROM sales s
            {sql_joins}
            {sql_where}
            GROUP BY dia, loja
            ORDER BY dia ASC;
        """
        
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_query, tuple(params))
            rows = cursor.fetchall()

        # Processar dados para o formato Chart.js
        labels = []
        datasets_data = {} 
        lojas = set()
        datas_dias = set()

        for dia, loja, faturamento in rows:
            dia_str = dia.isoformat()
            datas_dias.add(dia_str)
            lojas.add(loja)
            if loja not in datasets_data: datasets_data[loja] = {}
            datasets_data[loja][dia_str] = float(faturamento)

        labels = sorted(list(datas_dias))
        datasets = []
        for loja in sorted(list(lojas)):
            data = [datasets_data[loja].get(dia_label, 0) for dia_label in labels]
            datasets.append({'label': loja, 'data': data})

        return jsonify({'labels': labels, 'datasets': datasets})

    except Exception as e:
        print(f"ERRO [grafico-vendas-dia]: {e}", file=sys.stderr)
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn: release_connection(conn)

# --- NOVO - ENDPOINT GRÁFICO 2: Pedidos por Status (Pizza) ---
@app.route('/api/graficos/pedidos-por-status')
def grafico_pedidos_por_status():
    print("Recebida requisição em /api/graficos/pedidos-por-status")
    conn = None
    try:
        params, where_clauses, sql_joins = get_base_filters()
        # NÃO filtramos por status aqui, queremos ambos
        sql_where = "WHERE " + " AND ".join(where_clauses)

        sql_query = f"""
            SELECT s.sale_status_desc, COUNT(s.id) AS total_pedidos
            FROM sales s
            {sql_joins}
            {sql_where}
            GROUP BY s.sale_status_desc;
        """
        
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_query, tuple(params))
            rows = cursor.fetchall()
        
        labels = [row[0] for row in rows]
        data = [float(row[1]) for row in rows]

        return jsonify({'labels': labels, 'data': data})

    except Exception as e:
        print(f"ERRO [grafico-pedidos-status]: {e}", file=sys.stderr)
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn: release_connection(conn)

# --- ENDPOINT GRÁFICO 3: Pedidos por Canal (Barras Horizontais) ---
@app.route('/api/graficos/pedidos-por-canal')
def grafico_pedidos_por_canal():
    print("Recebida requisição em /api/graficos/pedidos-por-canal")
    conn = None
    try:
        params, where_clauses, sql_joins = get_base_filters()
        where_clauses.append("s.sale_status_desc = 'COMPLETED'") # Apenas concluídos
        sql_where = "WHERE " + " AND ".join(where_clauses)

        sql_query = f"""
            SELECT c.name, COUNT(s.id) AS total_pedidos
            FROM sales s
            {sql_joins}
            {sql_where}
            GROUP BY c.name
            ORDER BY total_pedidos DESC
            LIMIT 7; 
        """
        
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_query, tuple(params))
            rows = cursor.fetchall()
        
        # Invertemos para Chart.js (horizontal bar)
        labels = [row[0] for row in reversed(rows)]
        data = [float(row[1]) for row in reversed(rows)]

        return jsonify({'labels': labels, 'data': data})

    except Exception as e:
        print(f"ERRO [grafico-pedidos-canal]: {e}", file=sys.stderr)
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn: release_connection(conn)

# --- NOVO - ENDPOINT GRÁFICO 4: Pedidos por Hora (Barras Verticais) ---
@app.route('/api/graficos/pedidos-por-hora')
def grafico_pedidos_por_hora():
    print("Recebida requisição em /api/graficos/pedidos-por-hora")
    conn = None
    try:
        params, where_clauses, sql_joins = get_base_filters()
        where_clauses.append("s.sale_status_desc = 'COMPLETED'")
        sql_where = "WHERE " + " AND ".join(where_clauses)

        sql_query = f"""
            SELECT EXTRACT(HOUR FROM s.created_at) AS hora, COUNT(s.id) AS total_pedidos
            FROM sales s
            {sql_joins}
            {sql_where}
            GROUP BY hora;
        """
        
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_query, tuple(params))
            rows = cursor.fetchall()
        
        # Criar array de 24 horas para garantir que o gráfico mostre todas
        data_por_hora = {int(row[0]): float(row[1]) for row in rows}
        labels = [f"{h}h" for h in range(24)]
        data = [data_por_hora.get(h, 0) for h in range(24)]

        return jsonify({'labels': labels, 'data': data})

    except Exception as e:
        print(f"ERRO [grafico-pedidos-hora]: {e}", file=sys.stderr)
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn: release_connection(conn)


# --- Como rodar o servidor ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)