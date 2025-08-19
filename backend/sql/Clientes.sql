BEGIN;

-- 10.000 clientes demo
-- nro_cliente: 000001..010000
-- documento: 31000000001..3100010000 (11 dígitos)
-- email: cli000001@demo.local .. cli010000@demo.local

INSERT INTO cliente (
  nro_cliente, nombre, apellido, documento, telefono, email, direccion, estado, creado_en
)
SELECT
  LPAD(g::text, 6, '0')                                           AS nro_cliente,
  (ARRAY['Juan','María','Pedro','Lucía','Sofía','Diego','Ana','Carlos','Laura','Mateo'])
    [(g % 10) + 1]                                                AS nombre,
  (ARRAY['Pérez','García','López','Fernández','Rodríguez','Gómez','Martínez','Díaz','Sánchez','Romero'])
    [(g % 10) + 1]                                                AS apellido,
  (31000000000 + g)::text                                         AS documento,
  FORMAT('+54911%08s', g)                                         AS telefono,
  FORMAT('cli%06s@demo.local', g)                                 AS email,
  FORMAT('Calle %s Nº %s, Ciudad Demo', (g % 200) + 1, (g % 999) + 1) AS direccion,
  'activo'::estado_cliente_enum                                   AS estado,
  NOW() - ((g % 365)) * INTERVAL '1 day'                          AS creado_en
FROM generate_series(1, 10000) AS g
ON CONFLICT DO NOTHING;  -- por si ya existen algunos

-- Chequeo rápido:
-- SELECT COUNT(*) FROM cliente;
-- SELECT estado, COUNT(*) FROM cliente GROUP BY estado;

COMMIT;
