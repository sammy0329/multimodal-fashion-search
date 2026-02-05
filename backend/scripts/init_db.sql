-- Style Matcher: products 테이블 초기화
-- Supabase SQL Editor에서 실행

-- 1. products 테이블 생성
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_ko VARCHAR(255),
    price INTEGER NOT NULL CHECK (price >= 0),
    brand VARCHAR(100),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    style_tags TEXT[] DEFAULT '{}',
    color VARCHAR(50),
    image_url TEXT NOT NULL,
    description TEXT,
    material VARCHAR(100),
    season VARCHAR(20),
    data_source VARCHAR(50),
    is_soldout BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 인덱스
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_style_tags ON products USING GIN(style_tags);

-- 3. updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_products_updated_at ON products;
CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- 4. RLS (Row Level Security) 정책
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- 읽기: 모든 사용자 허용 (공개 상품 데이터)
CREATE POLICY "products_select_public"
    ON products
    FOR SELECT
    USING (true);

-- 쓰기: service_role만 허용 (백엔드 서버에서만 데이터 변경)
CREATE POLICY "products_insert_service"
    ON products
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "products_update_service"
    ON products
    FOR UPDATE
    USING (auth.role() = 'service_role');

CREATE POLICY "products_delete_service"
    ON products
    FOR DELETE
    USING (auth.role() = 'service_role');
