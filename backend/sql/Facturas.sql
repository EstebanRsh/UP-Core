BEGIN;

-- Parámetros: mes/año actuales (podés cambiar)
WITH params AS (
  SELECT EXTRACT(YEAR FROM CURRENT_DATE)::int AS anio,
         EXTRACT(MONTH FROM CURRENT_DATE)::int AS mes
),
base AS (
  SELECT
    c.id          AS contrato_id,
    c.plan_id     AS plan_id,
    p.mes,
    p.anio,
    DATE_TRUNC('month', MAKE_DATE(p.anio, p.mes, 1))::date                      AS periodo_inicio,
    (DATE_TRUNC('month', MAKE_DATE(p.anio, p.mes, 1)) + INTERVAL '1 month -1 day')::date AS periodo_fin
  FROM contrato c
  CROSS JOIN params p
),
faltantes AS (
  SELECT b.*
  FROM base b
  WHERE NOT EXISTS (
    SELECT 1
    FROM factura f
    WHERE f.contrato_id = b.contrato_id
      AND f.periodo_anio = b.anio
      AND f.periodo_mes  = b.mes
  )
),
ins AS (
  INSERT INTO factura (
    nro, contrato_id, periodo_mes, periodo_anio,
    periodo_inicio, periodo_fin,
    subtotal, mora, recargo, total,
    estado, emitida_en, vencimiento, pdf_path
  )
  SELECT
    -- nro temporal único (evita chocar UNIQUE en 'nro')
    to_char(b.anio, 'FM9999') || lpad(b.mes::text, 2, '0')
      || '-' || lpad(b.contrato_id::text, 6, '0') || '-TMP' AS nro,
    b.contrato_id,
    b.mes, b.anio,
    b.periodo_inicio, b.periodo_fin,
    pl.precio_mensual AS subtotal,
    NULL::numeric      AS mora,
    NULL::numeric      AS recargo,
    pl.precio_mensual  AS total,
    'borrador'::estado_factura_enum AS estado,
    NULL::timestamp    AS emitida_en,
    NULL::date         AS vencimiento,
    NULL::text         AS pdf_path
  FROM faltantes b
  JOIN plan pl ON pl.id = b.plan_id
  RETURNING id, periodo_mes, periodo_anio
)
-- Numeración definitiva: YYYYMM-ID
UPDATE factura f
SET nro = to_char(i.periodo_anio, 'FM9999')
          || lpad(i.periodo_mes::text, 2, '0')
          || '-' || lpad(f.id::text, 6, '0')
FROM ins i
WHERE f.id = i.id;

COMMIT;

