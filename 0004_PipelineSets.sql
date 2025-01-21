-- Add all the sets for each source

DECLARE @Order INT	 = 1000
,		@GroupID INT = 1;

WITH SetsData AS
(
SELECT	1000 AS SetId, 'Default Set' AS Description,@GroupID AS GroupId, @Order AS [Order], 1 AS IsActive UNION
-- Setid for Sun
SELECT	2000 AS SetId, 'Sun' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	3000 AS SetId, 'V1PSA' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	4000 AS SetId, 'Gears' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	5000 AS SetId, 'Cop' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	6000 AS SetId, 'iPOS' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	7000 AS SetId, 'D365' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	8000 AS SetId, 'Job Managment' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	9000 AS SetId, 'Job Manager' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

SELECT	10000 AS SetId, 'MyHR' AS Description,2 AS GroupId, @Order AS [Order], 1 AS IsActive UNION

)
MERGE	config.[PipelineSet]	tgt
USING	SetsData	src	ON	tgt.SetId		= src.SetId
WHEN	NOT MATCHED THEN
INSERT	(
		SetId	
,		Description
,		GroupId
,		[Order]
,		IsActive
,		CreatedBy
,		CreatedDate
		)
VALUES	(
		src.SetId
,		src.Description
,		src.GroupId
,		src.[Order]
,		src.IsActive
,		SYSTEM_USER
,		GETUTCDATE()
		)
WHEN	MATCHED AND
		(
		ISNULL(src.Description, '')		!= ISNULL(tgt.Description, '')
		OR	ISNULL(src.GroupId, '')		!= ISNULL(tgt.GroupId, '')
		OR	src.[Order]					!= tgt.[Order]
		OR	src.IsActive				!= tgt.IsActive
		)
		THEN
UPDATE
SET		Description	= src.Description
,		GroupId		= src.GroupId
,		[Order]		= src.[Order]
,		IsActive	= src.IsActive
,		UpdatedBy	= SYSTEM_USER
,		UpdatedDate	= GETUTCDATE();	