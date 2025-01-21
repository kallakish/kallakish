-- Add in initial Stages

DECLARE @ApplicationId INT = 1;

WITH Stage AS
(
SELECT	1 AS StageId, 'Ingest' AS StageName, 'Ingest data into bronze storage' AS StageDescription, @ApplicationId AS ApplicationId, 1 AS IsActive
UNION			
SELECT	2 AS StageId, 'Cleanse' AS StageName, 'Cleanse data from bronze into silver storage' AS StageDescription, @ApplicationId AS ApplicationId, 1 AS IsActive
UNION
SELECT	3 AS StageId, 'Quality' AS StageName, 'Transform data from silver into gold storage'	AS StageDescription, @ApplicationId AS ApplicationId, 1 AS IsActive
)
MERGE	config.[Stage]	tgt
USING	Stage		src	ON	tgt.StageId		= src.StageId
WHEN	NOT MATCHED THEN
INSERT	(
		StageId
,		StageName
,		StageDescription
,		ApplicationId
,		IsActive
,		CreatedBy
,		CreatedDate
		)
VALUES	(
		src.StageId
,		src.StageName
,		src.StageDescription
,		src.ApplicationId
,		src.IsActive
,		SYSTEM_USER
,		GETUTCDATE()
		)
WHEN	MATCHED AND
		(
			ISNULL(src.StageName, '')			!= ISNULL(tgt.StageName, '')
		OR	ISNULL(src.StageDescription, '')	!= ISNULL(tgt.StageDescription, '')
		OR	src.ApplicationId					!= tgt.ApplicationId
		OR	src.IsActive						!= tgt.IsActive
		)
		THEN
UPDATE
SET		StageName			= src.StageName
,		StageDescription	= src.StageDescription
,		ApplicationId		= src.ApplicationId
,		IsActive			= src.IsActive
,		UpdatedBy			= SYSTEM_USER
,		UpdatedDate			= GETUTCDATE()
WHEN 	NOT MATCHED BY SOURCE THEN
UPDATE	
SET		IsActive = 0;	

		