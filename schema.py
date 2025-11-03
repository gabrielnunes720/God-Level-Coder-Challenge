from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import date
from enum import Enum

# --- Definição das Métricas (O que medir) ---
# Baseado no database-schema.sql
class Metrica(str, Enum):
    faturamento_total = "faturamento_total"
    ticket_medio = "ticket_medio"
    total_pedidos = "total_pedidos"
    total_pedidos_cancelados = "total_pedidos_cancelados"
    taxa_cancelamento = "taxa_cancelamento"
    total_itens_vendidos = "total_itens_vendidos"
    total_descontos = "total_descontos"
    total_taxa_entrega = "total_taxa_entrega"
    tempo_preparo_medio_min = "tempo_preparo_medio_min"
    tempo_entrega_medio_min = "tempo_entrega_medio_min"
    faturamento_adicionais = "faturamento_adicionais"
    total_clientes_unicos = "total_clientes_unicos"

# --- Definição das Dimensões (Como agrupar) ---
# Baseado no database-schema.sql
class Dimensao(str, Enum):
    # Dimensões de Loja
    loja_nome = "loja_nome"
    cidade_loja = "cidade_loja"
    bairro_loja = "bairro_loja"
    estado_loja = "estado_loja"
    marca_nome = "marca_nome"
    sub_marca_nome = "sub_marca_nome"
    
    # Dimensões de Venda
    canal_nome = "canal_nome"
    tipo_canal = "tipo_canal"
    status_venda = "status_venda"
    origem_venda = "origem_venda"

    # Dimensões de Produto
    produto_nome = "produto_nome"
    produto_categoria = "produto_categoria"
    item_adicional_nome = "item_adicional_nome"
    grupo_opcao_nome = "grupo_opcao_nome"
    
    # Dimensões de Pagamento
    tipo_pagamento = "tipo_pagamento"
    
    # Dimensões de Entrega
    bairro_entrega = "bairro_entrega"
    cidade_entrega = "cidade_entrega"
    tipo_entregador = "tipo_entregador"
    tipo_entrega = "tipo_entrega"
    
    # Dimensões de Tempo
    dia = "dia"
    dia_semana = "dia_semana"
    mes = "mes"
    hora_dia = "hora_dia"
    data = "data" # Campo especial para filtro de data

class OperadorFiltro(str, Enum):
    eq = "eq"  # Igual (=)
    neq = "neq" # Diferente (!=)
    gt = "gt"  # Maior que (>)
    gte = "gte" # Maior ou igual (>=)
    lt = "lt"  # Menor que (<)
    lte = "lte" # Menor ou igual (<=)
    in_ = "in"  # Está em uma lista (IN)
    not_in = "not_in" # Não está em uma lista (NOT IN)
    like = "like" # Contém string (LIKE '%%')
    between = "between" # Entre duas datas/valores (BETWEEN)

class Ordem(str, Enum):
    asc = "ASC"  # Ascendente
    desc = "DESC" # Descendente

# --- Estrutura dos Filtros ---
class Filtro(BaseModel):
    campo: Dimensao = Field(..., description="O campo/dimensão para filtrar")
    operador: OperadorFiltro = Field(..., description="O operador de comparação")
    valor: Any = Field(..., description="O valor a ser comparado (pode ser string, int, lista, etc.)")

# --- O "CONTRATO" PRINCIPAL DA API ---
class QueryRequest(BaseModel):
    """
    Este é o objeto JSON que o Frontend (React) deve enviar
    para o nosso endpoint POST /api/v1/query
    """
    
    metrica: Metrica = Field(..., description="A métrica principal a ser calculada.")
    
    dimensoes: List[Dimensao] = Field(
        ..., 
        min_items=1,
        description="A lista de dimensões para agrupar (GROUP BY)."
    )
    
    filtros: Optional[List[Filtro]] = Field(
        default=[], 
        description="Lista de filtros a serem aplicados (WHERE)."
    )
    
    ordenar_por: str = Field(
        default="metrica", 
        description="Qual campo usar para ordenar (default: o valor da 'metrica')."
    )
    
    ordem: Ordem = Field(
        default=Ordem.desc, 
        description="Ordem ascendente (ASC) ou descendente (DESC)."
    )
    
    limite: int = Field(
        default=100, 
        description="Número máximo de resultados a retornar."
    )

    class Config:
        use_enum_values = True


# --- O Objeto de Resposta da API ---
class QueryResponse(BaseModel):
    """
    O que a nossa API irá retornar em formato JSON.
    """
    dados: List[dict] = Field(..., description="Os dados resultantes da consulta.")
    query_request: QueryRequest = Field(..., description="O 'pedido' original para referência.")