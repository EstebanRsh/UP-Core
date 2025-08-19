BEGIN;

INSERT INTO plan (nombre, vel_down, vel_up, precio_mensual, descripcion, activo, creado_en) VALUES
('Plan 50',   50,   25,  9000.00,  '50/25 Mbps',  TRUE, NOW()),
('Plan 100',  100,  50,  15000.00, '100/50 Mbps', TRUE, NOW()),
('Plan 200',  200,  100, 22000.00, '200/100 Mbps', TRUE, NOW()),
('Plan 300',  300,  150, 28000.00, '300/150 Mbps', TRUE, NOW()),
('Plan 500',  500,  250, 35000.00, '500/250 Mbps', TRUE, NOW()),
('Plan 700',  700,  350, 42000.00, '700/350 Mbps', TRUE, NOW()),
('Plan 1000', 1000, 500, 52000.00, '1000/500 Mbps', TRUE, NOW())
ON CONFLICT DO NOTHING;

-- (Opcional) Generar 20 planes de prueba automáticamente (Plan X)
-- INSERT INTO plan (nombre, vel_down, vel_up, precio_mensual, descripcion, activo, creado_en)
-- SELECT
--   format('Plan %s', 10 * g),
--   10 * g,
--   5 * g,
--   5000 + (g * 1000),
--   format('%s/%s Mbps', 10 * g, 5 * g),
--   TRUE,
--   NOW() - (g % 30) * INTERVAL '1 day'
-- FROM generate_series(8, 27) AS g
-- ON CONFLICT DO NOTHING;

COMMIT;
