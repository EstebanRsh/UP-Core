BEGIN;

INSERT INTO pago (factura_id, fecha, monto, metodo, referencia, comprobante_path, estado, creado_en)
SELECT
  f.id,
  NOW() - ((ROW_NUMBER() OVER (ORDER BY f.id)) % 7) * INTERVAL '1 day',
  (f.total * 0.5),
  'transferencia'::metodo_pago_enum,
  format('TX-%s', f.id),
  NULL,
  'confirmado'::estado_pago_enum,
  NOW()
FROM factura f
ORDER BY f.id
LIMIT 50
ON CONFLICT DO NOTHING;

COMMIT;
