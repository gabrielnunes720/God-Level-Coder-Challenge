-- 1. Índice para o filtro de DATA e HORA (o mais importante!)
CREATE INDEX IF NOT EXISTS idx_sales_created_at_hora_dia ON sales (EXTRACT(HOUR FROM created_at), EXTRACT(ISODOW FROM created_at));

-- 2. Índice para o filtro de NOME DO CANAL
CREATE INDEX IF NOT EXISTS idx_channels_name ON channels (name);

-- 3. Índice para o filtro de NOME DA SUB-MARCA (Loja)
CREATE INDEX IF NOT EXISTS idx_sub_brands_name ON sub_brands (name);

-- 4. Índices para as colunas de "JOIN" (chaves estrangeiras)
CREATE INDEX IF NOT EXISTS idx_sales_store_id ON sales (store_id);
CREATE INDEX IF NOT EXISTS idx_sales_channel_id ON sales (channel_id);
CREATE INDEX IF NOT EXISTS idx_product_sales_sale_id ON product_sales (sale_id);
CREATE INDEX IF NOT EXISTS idx_product_sales_product_id ON product_sales (product_id);
CREATE INDEX IF NOT EXISTS idx_stores_sub_brand_id ON stores (sub_brand_id);
