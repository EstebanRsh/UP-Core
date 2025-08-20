WITH u AS (
  SELECT id AS usuario_id, row_number() OVER (ORDER BY id) rn
  FROM usuario
  WHERE role = 'cliente'::role_enum
),
c AS (
  SELECT id AS cliente_id, row_number() OVER (ORDER BY id) rn
  FROM cliente
  WHERE usuario_id IS NULL
)
UPDATE cliente
SET usuario_id = u.usuario_id
FROM u
JOIN c ON c.rn = u.rn
WHERE cliente.id = c.cliente_id;
