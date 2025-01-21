-- Add in initial Groups

DECLARE @DefaultGroupOrder INT = 1000;

WITH Groups AS
(
SELECT	1 AS GroupId, 'default' AS GroupName, 'Default Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	2 AS GroupId, 'Sun' AS GroupName, 'Sun Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	3 AS GroupId, 'V1PSA' AS GroupName, 'V1PSA Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	4 AS GroupId, 'Gears' AS GroupName, 'Gears Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	5 AS GroupId, 'Cop' AS GroupName, 'Cop Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	6 AS GroupId, 'iPOS' AS GroupName, 'iPOS Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	7 AS GroupId, 'D365' AS GroupName, 'D365 Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	8 AS GroupId, 'Job Managment' AS GroupName, 'Job Managment Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	9 AS GroupId, 'Job Manager' AS GroupName, 'Job Manager Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive union
SELECT	10 AS GroupId, 'MyHR' AS GroupName, 'MyHR Group' AS Description, @DefaultGroupOrder AS [Order], 1 AS IsActive
)

MERGE	config.[PipelineGroup]	tgt
USING	Groups	src	ON	tgt.GroupId		= src.GroupId
WHEN	NOT MATCHED THEN
INSERT	(
		GroupId	
,		GroupName
,		Description
,		[Order]
,		IsActive
,		CreatedBy
,		CreatedDate
		)
VALUES	(
		src.GroupId
,		src.GroupName
,		src.Description
,		src.[Order]
,		src.IsActive
,		SYSTEM_USER
,		GETUTCDATE()
		)
WHEN	MATCHED AND
		(
			ISNULL(src.GroupName, '')	!= ISNULL(tgt.GroupName, '')
		OR	ISNULL(src.Description, '')	!= ISNULL(tgt.Description, '')
		OR	src.[Order]					!= tgt.[Order]
		OR	src.IsActive				!= tgt.IsActive
		)
		THEN
UPDATE
SET		GroupName	= src.GroupName
,		Description	= src.Description
,		[Order]		= src.[Order]
,		IsActive	= src.IsActive
,		UpdatedBy	= SYSTEM_USER
,		UpdatedDate	= GETUTCDATE()
WHEN 	NOT MATCHED BY SOURCE THEN
UPDATE	
SET		IsActive = 0
,		UpdatedBy	= SYSTEM_USER
,		UpdatedDate	= GETUTCDATE();	