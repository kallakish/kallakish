-- Add in Pipelines for Ingest Sun

DECLARE @SunIngestPipeline 	VARCHAR(100) 	= 'PL_Sun_SQL_To_Bronze'
,		@SunCleansePipeline 	VARCHAR(100) 	= 'PL_Sun_Bronze_To_Silver'
,		@SunCleanseParquetPipeline 	VARCHAR(100) 	= 'PL_Sun_Bronze_To_Silver_Parquet'
,		@SunGoldPipeline 	VARCHAR(100)  	= 'PL_Sun_Silver_To_Gold'
,		@SunIngestStageId	INT 			= 1
,		@SunCleanseStageId	INT 			= 2
,		@SunGoldStageId	INT 			= 3
,		@SunActive          	INT             = $(SunActive)
,		@SunActiveZZZZ          	INT         = $(SunActive)
,		@SunParquetActive		INT			= $(SunParquetActive)
,		@SunGoldPipelineFirstQueryFrom   VARCHAR(100)    = '2023-10-01 00:00:00' -- post release date to skip historical data;
;

WITH Pipeline AS
(
-- Ingest
SELECT	1 AS PipelineId, @SunIngestPipeline AS PipelineName, 'Sun Ingest XXX' AS PipelineDescription,2 AS SetId, @SunIngestStageId AS StageId, 1000 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION
SELECT	2 AS PipelineId, @SunIngestPipeline AS PipelineName, 'Sun Ingest VVVV' AS PipelineDescription,3 AS SetId, @SunIngestStageId AS StageId, 1020 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION
SELECT	3 AS PipelineId, @SunIngestPipeline AS PipelineName, 'Sun Ingest ZZZZ' AS PipelineDescription,4 AS SetId, @SunIngestStageId AS StageId, 1030 AS ExecutionOrder, 'I' AS ExecutionType, @SunActiveZZZZ  AS IsActive UNION
SELECT	4 AS PipelineId, @SunIngestPipeline AS PipelineName, 'Sun Ingest ZZZZ' AS PipelineDescription,5 AS SetId, @SunIngestStageId AS StageId, 1040 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION
SELECT	5 AS PipelineId, @SunIngestPipeline AS PipelineName, 'Sun Ingest ZZZZ' AS PipelineDescription,6 AS SetId, @SunIngestStageId AS StageId, 1050 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION

-- Cleanse
SELECT	6 AS PipelineId, @SunCleansePipeline AS PipelineName, 'Sun Cleanse CMC' AS PipelineDescription,2 AS SetId, @SunCleanseStageId AS StageId, 1010 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION
SELECT	7 AS PipelineId, @SunCleansePipeline AS PipelineName, 'Sun Cleanse VVVV' AS PipelineDescription,3 AS SetId, @SunCleanseStageId AS StageId, 1020 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION
SELECT	8 AS PipelineId, @SunCleansePipeline AS PipelineName, 'Sun Cleanse ZZZZ' AS PipelineDescription,4 AS SetId, @SunCleanseStageId AS StageId, 1030 AS ExecutionOrder, 'I' AS ExecutionType, @SunActiveZZZZ  AS IsActive UNION
SELECT	9 AS PipelineId, @SunCleansePipeline AS PipelineName, 'Sun Cleanse ZZZZ' AS PipelineDescription,5 AS SetId, @SunCleanseStageId AS StageId, 1040 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION
SELECT	10 AS PipelineId, @SunCleansePipeline AS PipelineName, 'Sun Cleanse ZZZZ' AS PipelineDescription,6 AS SetId, @SunCleanseStageId AS StageId, 1050 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive  AS IsActive UNION

--Gold
SELECT	11 AS PipelineId, @SunGoldPipeline AS PipelineName, 'Sun Gold CMC' AS PipelineDescription,2 AS SetId, @SunGoldStageId AS StageId, 10 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive AS IsActive UNION
SELECT	12 AS PipelineId, @SunGoldPipeline AS PipelineName, 'Sun Gold VVVV' AS PipelineDescription,3 AS SetId, @SunGoldStageId AS StageId, 20 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive AS IsActive UNION
SELECT	13 AS PipelineId, @SunGoldPipeline AS PipelineName, 'Sun Gold ZZZZ' AS PipelineDescription,4 AS SetId, @SunGoldStageId AS StageId, 30 AS ExecutionOrder, 'I' AS ExecutionType, @SunActiveZZZZ AS IsActive UNION
SELECT	14 AS PipelineId, @SunGoldPipeline AS PipelineName, 'Sun Gold ZZZZ' AS PipelineDescription,5 AS SetId, @SunGoldStageId AS StageId, 40 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive AS IsActive UNION
SELECT	15 AS PipelineId, @SunGoldPipeline AS PipelineName, 'Sun Gold ZZZZ' AS PipelineDescription,6 AS SetId, @SunGoldStageId AS StageId, 50 AS ExecutionOrder, 'I' AS ExecutionType, @SunActive AS IsActive
)
MERGE	config.Pipeline	tgt
USING	Pipeline		src	ON	tgt.PipelineId		= src.PipelineId
WHEN	NOT MATCHED THEN
INSERT	(
		PipelineId
,		PipelineName
,		PipelineDescription
,		SetId
,		StageId
,		ExecutionOrder
,		ExecutionType
,		IsActive
,		CreatedBy
,		CreatedDate
		)
VALUES	(
		src.PipelineId
,		src.PipelineName
,		src.PipelineDescription
,		src.SetId
,		src.StageId
,		src.ExecutionOrder
,		src.ExecutionType
,		src.IsActive
,		SYSTEM_USER
,		GETUTCDATE()
		)
WHEN	MATCHED AND
		(
			ISNULL(src.PipelineName, '')		!= ISNULL(tgt.PipelineName, '')
		OR	ISNULL(src.PipelineDescription, '')	!= ISNULL(tgt.PipelineDescription, '')
		OR	src.ExecutionOrder					!= tgt.ExecutionOrder
		OR	ISNULL(src.ExecutionType, '')		!= ISNULL(tgt.ExecutionType, '')
		OR	src.SetId							!= tgt.SetId
		OR	src.StageId							!= tgt.StageId
		OR	src.IsActive						!= tgt.IsActive
		)
		THEN
UPDATE
SET		PipelineName		= src.PipelineName
,		PipelineDescription	= src.PipelineDescription
,		SetId				= src.SetId
,		StageId				= src.StageId
,		ExecutionOrder		= src.ExecutionOrder
,		ExecutionType		= src.ExecutionType
,		IsActive			= src.IsActive
,		UpdatedBy			= SYSTEM_USER
,		UpdatedDate			= GETUTCDATE();

