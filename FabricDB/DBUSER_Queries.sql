SELECT name, type_desc
FROM sys.database_principals
WHERE name = '<your-spn-display-name>';

SELECT r.name AS role_name, p.name AS member_name
FROM sys.database_role_members m
JOIN sys.database_principals r ON m.role_principal_id = r.principal_id
JOIN sys.database_principals p ON m.member_principal_id = p.principal_id
WHERE p.name = '<your-spn-display-name>';
