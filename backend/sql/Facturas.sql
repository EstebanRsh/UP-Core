BEGIN;

WITH base AS (
  SELECT c.id AS contrato_id,
         c.plan_id,
         8  AS periodo_mes,
         2025 AS periodo_anio,
         DATE '2025-08-01' AS periodo_inicio,
         DATE '2025-08-31' AS periodo_fin,
         p.precio_mensual AS subtotal
  FROM contrato c
  JOIN plan p ON p.id = c.plan_id
  WHERE c.id BETWEEN 1 AND 300
),
ins AS (
  INSERT INTO factura (
    nro, contrato_id, periodo_mes, periodo_anio,
    periodo_inicio, periodo_fin,
    subtotal, mora, recargo, total,
    estado, emitida_en, vencimiento, pdf_path
  )
  SELECT
    -- nro temporal único por contrato+periodo (evita chocar UNIQUE)
    to_char(periodo_anio, 'FM9999') || lpad(periodo_mes::text, 2, '0')
      || '-' || lpad(contrato_id::text, 6, '0') || '-TMP' AS nro,
    contrato_id,
    periodo_mes, periodo_anio,
    periodo_inicio, periodo_fin,
    subtotal,
    NULL::numeric,            -- mora
    NULL::numeric,            -- recargo
    subtotal,                 -- total inicial = subtotal
    'borrador'::estado_factura_enum,
    NULL::timestamp,          -- emitida_en
    NULL::date,               -- vencimiento
    NULL::text                -- pdf_path
  FROM base
  ON CONFLICT DO NOTHING
  RETURNING id, contrato_id, periodo_mes, periodo_anio
)
UPDATE factura f
SET nro = to_char(i.periodo_anio, 'FM9999')
          || lpad(i.periodo_mes::text, 2, '0')
          || '-' || lpad(f.id::text, 6, '0')
FROM ins i
WHERE f.id = i.id;

-- Por si te quedó una factura vieja con 'PENDIENTE' de un intento anterior:
UPDATE factura f
SET nro = to_char(f.periodo_anio, 'FM9999')
          || lpad(f.periodo_mes::text, 2, '0')
          || '-' || lpad(f.id::text, 6, '0')
WHERE f.nro = 'PENDIENTE';

COMMIT;
