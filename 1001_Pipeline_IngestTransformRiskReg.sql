-- Add in Pipelines for Ingest RiskReg...

DECLARE @RiskRegIngestPipeline 	VARCHAR(100) 	= 'PL_xxxx_SQL_To_Bronze'
,		@RiskRegCleansePipeline 	VARCHAR(100) 	= 'PL_RiskReg_Bronze_To_Silver'
,		@RiskRegCleanseParquetPipeline 	VARCHAR(100) 	= 'PL_RiskReg_Bronze_To_Silver_Parquet'
,		@RiskRegGoldPipeline 	VARCHAR(100)  	= 'PL_RiskReg_Silver_To_Gold'
,		@RiskRegIngestStageId	INT 			= 1
,		@RiskRegCleanseStageId	INT 			= 2
,		@RiskRegGoldStageId	INT 			= 3
,		@RiskRegActive          	INT             = $(RiskRegActive)
,		@RiskRegActiveZZZZ          	INT         = $(RiskRegActive)
,		@RiskRegParquetActive		INT			= $(RiskRegParquetActive)
,		@RiskRegGoldPipelineFirstQueryFrom   VARCHAR(100)    = '2025-01-01 00:00:00' -- post release date to skip historical data;
;

WITH Pipeline AS
(
-- Ingest
SELECT	1 AS PipelineId, @RiskRegIngestPipeline AS PipelineName, 'RiskReg Ingest XXX' AS PipelineDescription,2 AS SetId, @RiskRegIngestStageId AS StageId, 1000 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION
SELECT	2 AS PipelineId, @RiskRegIngestPipeline AS PipelineName, 'RiskReg Ingest VVVV' AS PipelineDescription,3 AS SetId, @RiskRegIngestStageId AS StageId, 1020 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION
SELECT	3 AS PipelineId, @RiskRegIngestPipeline AS PipelineName, 'RiskReg Ingest ZZZZ' AS PipelineDescription,4 AS SetId, @RiskRegIngestStageId AS StageId, 1030 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActiveZZZZ  AS IsActive UNION
SELECT	4 AS PipelineId, @RiskRegIngestPipeline AS PipelineName, 'RiskReg Ingest ZZZZ' AS PipelineDescription,5 AS SetId, @RiskRegIngestStageId AS StageId, 1040 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION
SELECT	5 AS PipelineId, @RiskRegIngestPipeline AS PipelineName, 'RiskReg Ingest ZZZZ' AS PipelineDescription,6 AS SetId, @RiskRegIngestStageId AS StageId, 1050 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION

-- Cleanse
SELECT	6 AS PipelineId, @RiskRegCleansePipeline AS PipelineName, 'RiskReg Cleanse CMC' AS PipelineDescription,2 AS SetId, @RiskRegCleanseStageId AS StageId, 1010 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION
SELECT	7 AS PipelineId, @RiskRegCleansePipeline AS PipelineName, 'RiskReg Cleanse VVVV' AS PipelineDescription,3 AS SetId, @RiskRegCleanseStageId AS StageId, 1020 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION
SELECT	8 AS PipelineId, @RiskRegCleansePipeline AS PipelineName, 'RiskReg Cleanse ZZZZ' AS PipelineDescription,4 AS SetId, @RiskRegCleanseStageId AS StageId, 1030 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActiveZZZZ  AS IsActive UNION
SELECT	9 AS PipelineId, @RiskRegCleansePipeline AS PipelineName, 'RiskReg Cleanse ZZZZ' AS PipelineDescription,5 AS SetId, @RiskRegCleanseStageId AS StageId, 1040 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION
SELECT	10 AS PipelineId, @RiskRegCleansePipeline AS PipelineName, 'RiskReg Cleanse ZZZZ' AS PipelineDescription,6 AS SetId, @RiskRegCleanseStageId AS StageId, 1050 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive  AS IsActive UNION

--Gold
SELECT	11 AS PipelineId, @RiskRegGoldPipeline AS PipelineName, 'RiskReg Gold CMC' AS PipelineDescription,2 AS SetId, @RiskRegGoldStageId AS StageId, 10 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive AS IsActive UNION
SELECT	12 AS PipelineId, @RiskRegGoldPipeline AS PipelineName, 'RiskReg Gold VVVV' AS PipelineDescription,3 AS SetId, @RiskRegGoldStageId AS StageId, 20 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive AS IsActive UNION
SELECT	13 AS PipelineId, @RiskRegGoldPipeline AS PipelineName, 'RiskReg Gold ZZZZ' AS PipelineDescription,4 AS SetId, @RiskRegGoldStageId AS StageId, 30 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActiveZZZZ AS IsActive UNION
SELECT	14 AS PipelineId, @RiskRegGoldPipeline AS PipelineName, 'RiskReg Gold ZZZZ' AS PipelineDescription,5 AS SetId, @RiskRegGoldStageId AS StageId, 40 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive AS IsActive UNION
SELECT	15 AS PipelineId, @RiskRegGoldPipeline AS PipelineName, 'RiskReg Gold ZZZZ' AS PipelineDescription,6 AS SetId, @RiskRegGoldStageId AS StageId, 50 AS ExecutionOrder, 'I' AS ExecutionType, @RiskRegActive AS IsActive
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

