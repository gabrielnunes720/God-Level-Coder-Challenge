

from sqlalchemy import (
    Table, Column, Integer, String, Float, DateTime, Boolean, MetaData,
    func, case, select, and_, Numeric, Date, CHAR
)
from .schema import QueryRequest, Metrica, Dimensao, Filtro, OperadorFiltro

# --- 1. Definição do Schema do Banco (Espelho do database-schema.sql) ---
metadata = MetaData()

# Mapeamos TODAS as tabelas e colunas relevantes do schema real
t_brands = Table('brands', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)
t_sub_brands = Table('sub_brands', metadata,
    Column('id', Integer, primary_key=True),
    Column('brand_id', Integer),
    Column('name', String),
)
t_stores = Table('stores', metadata,
    Column('id', Integer, primary_key=True),
    Column('brand_id', Integer),
    Column('sub_brand_id', Integer),
    Column('name', String),
    Column('city', String),
    Column('state', String),
    Column('district', String),
)
t_channels = Table('channels', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('type', CHAR),
)
t_categories = Table('categories', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('type', CHAR),
)
t_products = Table('products', metadata,
    Column('id', Integer, primary_key=True),
    Column('category_id', Integer),
    Column('name', String),
)
t_option_groups = Table('option_groups', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)
t_items = Table('items', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
)
t_customers = Table('customers', metadata,
    Column('id', Integer, primary_key=True),
)
t_sales = Table('sales', metadata,
    Column('id', Integer, primary_key=True),
    Column('store_id', Integer),
    Column('sub_brand_id', Integer),
    Column('customer_id', Integer),
    Column('channel_id', Integer),
    Column('created_at', DateTime),
    Column('sale_status_desc', String),
    Column('total_amount_items', Numeric),
    Column('total_discount', Numeric),
    Column('total_increase', Numeric),
    Column('delivery_fee', Numeric),
    Column('service_tax_fee', Numeric),
    Column('total_amount', Numeric),
    Column('value_paid', Numeric),
    Column('production_seconds', Integer),
    Column('delivery_seconds', Integer),
    Column('origin', String),
)
t_product_sales = Table('product_sales', metadata,
    Column('id', Integer, primary_key=True),
    Column('sale_id', Integer),
    Column('product_id', Integer),
    Column('quantity', Float),
)
t_item_product_sales = Table('item_product_sales', metadata,
    Column('id', Integer, primary_key=True),
    Column('product_sale_id', Integer),
    Column('item_id', Integer),
    Column('option_group_id', Integer),
    Column('additional_price', Float),
)
t_delivery_sales = Table('delivery_sales', metadata,
    Column('id', Integer, primary_key=True),
    Column('sale_id', Integer),
    Column('courier_type', String),
    Column('delivery_type', String),
)
t_delivery_addresses = Table('delivery_addresses', metadata,
    Column('id', Integer, primary_key=True),
    Column('sale_id', Integer),
    Column('neighborhood', String),
    Column('city', String),
)
t_payment_types = Table('payment_types', metadata,
    Column('id', Integer, primary_key=True),
    Column('description', String),
)
t_payments = Table('payments', metadata,
    Column('id', Integer, primary_key=True),
    Column('sale_id', Integer),
    Column('payment_type_id', Integer),
)

# --- 2. Mapas de Tradução (O "Cérebro") ---

# Mapeia a 'Metrica' (amigável) para a coluna/função SQL (SQLAlchemy)
METRIC_MAP = {
    Metrica.faturamento_total: func.sum(t_sales.c.total_amount),
    Metrica.ticket_medio: func.avg(t_sales.c.total_amount),
    Metrica.total_pedidos: func.count(t_sales.c.id),
    Metrica.total_pedidos_cancelados: func.count(
        case((t_sales.c.sale_status_desc == 'CANCELLED', t_sales.c.id), else_=None)
    ),
    Metrica.taxa_cancelamento: (
        func.count(case((t_sales.c.sale_status_desc == 'CANCELLED', t_sales.c.id), else_=None)) * 100.0
        / func.count(t_sales.c.id)
    ),
    Metrica.total_itens_vendidos: func.sum(t_product_sales.c.quantity),
    Metrica.total_descontos: func.sum(t_sales.c.total_discount),
    Metrica.total_taxa_entrega: func.sum(t_sales.c.delivery_fee),
    Metrica.tempo_preparo_medio_min: func.avg(t_sales.c.production_seconds / 60.0),
    Metrica.tempo_entrega_medio_min: func.avg(t_sales.c.delivery_seconds / 60.0),
    Metrica.faturamento_adicionais: func.sum(t_item_product_sales.c.additional_price),
    Metrica.total_clientes_unicos: func.count(t_sales.c.customer_id.distinct()),
}

# Mapeia a 'Dimensao' (amigável) para a coluna SQL (SQLAlchemy)
DIMENSION_MAP = {
    Dimensao.loja_nome: t_stores.c.name,
    Dimensao.cidade_loja: t_stores.c.city,
    Dimensao.bairro_loja: t_stores.c.district,
    Dimensao.estado_loja: t_stores.c.state,
    Dimensao.marca_nome: t_brands.c.name,
    Dimensao.sub_marca_nome: t_sub_brands.c.name,
    Dimensao.canal_nome: t_channels.c.name,
    Dimensao.tipo_canal: t_channels.c.type,
    Dimensao.produto_nome: t_products.c.name,
    Dimensao.produto_categoria: t_categories.c.name,
    Dimensao.item_adicional_nome: t_items.c.name,
    Dimensao.grupo_opcao_nome: t_option_groups.c.name,
    Dimensao.tipo_pagamento: t_payment_types.c.description,
    Dimensao.status_venda: t_sales.c.sale_status_desc,
    Dimensao.origem_venda: t_sales.c.origin,
    Dimensao.bairro_entrega: t_delivery_addresses.c.neighborhood,
    Dimensao.cidade_entrega: t_delivery_addresses.c.city,
    Dimensao.tipo_entregador: t_delivery_sales.c.courier_type,
    Dimensao.tipo_entrega: t_delivery_sales.c.delivery_type,
    Dimensao.dia: func.date(t_sales.c.created_at),
    Dimensao.dia_semana: func.to_char(t_sales.c.created_at, 'Day'),
    Dimensao.mes: func.to_char(t_sales.c.created_at, 'YYYY-MM'),
    Dimensao.hora_dia: func.extract('hour', t_sales.c.created_at),
    Dimensao.data: t_sales.c.created_at 
}


# --- 3. O Construtor da Query (A Lógica Principal) ---

def build_analytics_query(request: QueryRequest):
    """
    Recebe o 'contrato' (QueryRequest) e constrói dinamicamente
    uma query SQLAlchemy segura e otimizada.
    """
    
    # --- Passo 1: Selecionar a Métrica ---
    metric_sql = METRIC_MAP.get(request.metrica)
    if metric_sql is None:
        raise ValueError(f"Métrica inválida: {request.metrica}")
    
    query = select(metric_sql.label("metrica"))
    
    # --- Passo 2 & 3: Dimensões e JOINs necessários ---
    dimensions_sql = []
    required_joins = {t_sales} 
    dim_fields = set(d.value for d in request.dimensoes)
    filter_fields = set(f.campo.value for f in request.filtros)
    all_fields = dim_fields.union(filter_fields)

    # Função auxiliar para adicionar joins
    def add_join(table, condition):
        if table not in required_joins:
            required_joins.add(table)
            return (table, condition)
        return None

    join_conditions = []

    # Mapeia campos (dimensões/filtros) para as tabelas e joins que eles precisam
    # Esta é a lógica central para otimizar os joins
    if any(f in all_fields for f in ['loja_nome', 'cidade_loja', 'bairro_loja', 'estado_loja', 'marca_nome', 'sub_marca_nome']):
        join_conditions.append(add_join(t_stores, t_sales.c.store_id == t_stores.c.id))
    
    if 'sub_marca_nome' in all_fields:
        join_conditions.append(add_join(t_sub_brands, t_sales.c.sub_brand_id == t_sub_brands.c.id))
        
    if 'marca_nome' in all_fields:
        # Precisa de join em stores E sub_brands para chegar em brands
        join_conditions.append(add_join(t_stores, t_sales.c.store_id == t_stores.c.id))
        join_conditions.append(add_join(t_brands, t_stores.c.brand_id == t_brands.c.id))

    if any(f in all_fields for f in ['canal_nome', 'tipo_canal']):
        join_conditions.append(add_join(t_channels, t_sales.c.channel_id == t_channels.c.id))

    if any(f in all_fields for f in ['bairro_entrega', 'cidade_entrega']):
        join_conditions.append(add_join(t_delivery_addresses, t_sales.c.id == t_delivery_addresses.c.sale_id, True)) # LEFT JOIN

    if any(f in all_fields for f in ['tipo_entregador', 'tipo_entrega']):
        join_conditions.append(add_join(t_delivery_sales, t_sales.c.id == t_delivery_sales.c.sale_id, True)) # LEFT JOIN

    if 'tipo_pagamento' in all_fields:
        join_conditions.append(add_join(t_payments, t_sales.c.id == t_payments.c.sale_id))
        join_conditions.append(add_join(t_payment_types, t_payments.c.payment_type_id == t_payment_types.c.id))

    # Joins para Produtos/Itens (mais complexos)
    product_fields = ['produto_nome', 'produto_categoria', 'item_adicional_nome', 'grupo_opcao_nome']
    if any(f in all_fields for f in product_fields) or request.metrica in [Metrica.total_itens_vendidos, Metrica.faturamento_adicionais]:
        join_conditions.append(add_join(t_product_sales, t_sales.c.id == t_product_sales.c.sale_id))

    if any(f in all_fields for f in ['produto_nome', 'produto_categoria']):
        join_conditions.append(add_join(t_products, t_product_sales.c.product_id == t_products.c.id))

    if 'produto_categoria' in all_fields:
        join_conditions.append(add_join(t_categories, t_products.c.category_id == t_categories.c.id))

    if any(f in all_fields for f in ['item_adicional_nome', 'grupo_opcao_nome']) or request.metrica == Metrica.faturamento_adicionais:
        join_conditions.append(add_join(t_item_product_sales, t_product_sales.c.id == t_item_product_sales.c.product_sale_id, True)) # LEFT JOIN

    if 'item_adicional_nome' in all_fields:
        join_conditions.append(add_join(t_items, t_item_product_sales.c.item_id == t_items.c.id, True)) # LEFT JOIN
    
    if 'grupo_opcao_nome' in all_fields:
         join_conditions.append(add_join(t_option_groups, t_item_product_sales.c.option_group_id == t_option_groups.c.id, True)) # LEFT JOIN

    # Adiciona as dimensões ao SELECT
    for dim in request.dimensoes:
        dim_sql = DIMENSION_MAP.get(dim)
        if dim_sql is None:
            raise ValueError(f"Dimensão inválida: {dim}")
        dimensions_sql.append(dim_sql.label(dim.value))
    
    query = query.add_columns(*dimensions_sql)

    # --- Passo 4: Construir a cláusula FROM (com JOINs) ---
    join_chain = t_sales
    for j in join_conditions:
        if j: # Ignora Nones (joins já adicionados)
            table, condition, *isouter = j
            join_chain = join_chain.join(table, condition, isouter=isouter)

    query = query.select_from(join_chain)

    # --- Passo 5: Construir a cláusula WHERE (Filtros) ---
    filters_sql = []
    for f in request.filtros:
        col_sql = DIMENSION_MAP.get(f.campo)
        if col_sql is None:
            raise ValueError(f"Campo de filtro inválido: {f.campo}")

        if f.operador == OperadorFiltro.eq: filters_sql.append(col_sql == f.valor)
        elif f.operador == OperadorFiltro.neq: filters_sql.append(col_sql != f.valor)
        elif f.operador == OperadorFiltro.gt: filters_sql.append(col_sql > f.valor)
        elif f.operador == OperadorFiltro.gte: filters_sql.append(col_sql >= f.valor)
        elif f.operador == OperadorFiltro.lt: filters_sql.append(col_sql < f.valor)
        elif f.operador == OperadorFiltro.lte: filters_sql.append(col_sql <= f.valor)
        elif f.operador == OperadorFiltro.in_: filters_sql.append(col_sql.in_(f.valor))
        elif f.operador == OperadorFiltro.not_in: filters_sql.append(col_sql.notin_(f.valor))
        elif f.operador == OperadorFiltro.like: filters_sql.append(col_sql.like(f"%{f.valor}%"))
        elif f.operador == OperadorFiltro.between:
            if isinstance(f.valor, (list, tuple)) and len(f.valor) == 2:
                filters_sql.append(col_sql.between(f.valor[0], f.valor[1]))
            else:
                raise ValueError("Operador 'between' exige uma lista com 2 valores")
    
    if filters_sql:
        query = query.where(and_(*filters_sql))

    # --- Passo 6: Construir GROUP BY, ORDER BY, LIMIT ---
    if dimensions_sql:
        query = query.group_by(*dimensions_sql)

    # Ordenação
    order_col_sql = None
    if request.ordenar_por == "metrica":
        order_col_sql = "metrica"
    elif request.ordenar_por in dim_fields:
        order_col_sql = DIMENSION_MAP.get(Dimensao(request.ordenar_por))
    
    if order_col_sql is None:
        raise ValueError(f"Campo de ordenação inválido: {request.ordenar_por}")

    order_func = func.desc if request.ordem == Ordem.desc else func.asc
    query = query.order_by(order_func(order_col_sql))
    
    query = query.limit(request.limite)

    # --- Passo 7: Retornar a query pronta ---
    return query