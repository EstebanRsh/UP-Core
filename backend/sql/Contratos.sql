BEGIN;

-- requiere que existan clientes con id 1..300 y planes con id 1..5
INSERT INTO contrato (cliente_id, plan_id, direccion_instalacion, fecha_alta, estado)
SELECT
  c_id,
  ((c_id - 1) % 5) + 1 AS plan_id,
  format('Calle Conexión %s, Ciudad Demo', c_id),
  CURRENT_DATE - ((c_id % 30))::int,
  'activo'::estado_contrato_enum
FROM generate_series(1, 300) AS c_id
ON CONFLICT DO NOTHING;

COMMIT;
