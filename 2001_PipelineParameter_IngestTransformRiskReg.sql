-- Add in initial Pipeline Params for Ingest RiskReg..
-- refer to 1001_Pipeline_IngestRiskReg.sql for PipelineID
DECLARE @RiskRegVersion VARCHAR(3)   	= '$(Version)';

WITH PipelineParam AS
(
	-- Ingest RiskReg
SELECT   1 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   1 AS PipelineId,  'SourceSubName' AS ParameterName,  'xxxx' AS ParameterValue,  1 AS IsActive UNION 
SELECT   1 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   1 AS PipelineId,  'OlderThanValue' AS ParameterName,  'Init' AS ParameterValue,  1 AS IsActive UNION 

SELECT   2 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   2 AS PipelineId,  'SourceSubName' AS ParameterName,  'YYYY' AS ParameterValue,  1 AS IsActive UNION 
SELECT   2 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   2 AS PipelineId,  'OlderThanValue' AS ParameterName,  'Init' AS ParameterValue,  1 AS IsActive UNION

SELECT   3 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   3 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION 
SELECT   3 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION
SELECT   3 AS PipelineId,  'OlderThanValue' AS ParameterName,  'Init' AS ParameterValue,  1 AS IsActive UNION 

SELECT   4 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   4 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION 
SELECT   4 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   4 AS PipelineId,  'OlderThanValue' AS ParameterName,  'Init' AS ParameterValue,  1 AS IsActive UNION

SELECT   5 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   5 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION
SELECT   5 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION
SELECT   5 AS PipelineId,  'OlderThanValue' AS ParameterName,  'Init' AS ParameterValue,  1 AS IsActive UNION

-- Transform RiskReg
SELECT   6 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   6 AS PipelineId,  'SourceSubName' AS ParameterName,  'xxxx' AS ParameterValue,  1 AS IsActive UNION 
SELECT   6 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION

SELECT   7 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   7 AS PipelineId,  'SourceSubName' AS ParameterName,  'YYYY' AS ParameterValue,  1 AS IsActive UNION 
SELECT   7 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION

SELECT   8 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   8 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION 
SELECT   8 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 

SELECT   9 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   9 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION 
SELECT   9 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION

SELECT   10 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   10 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION
SELECT   10 AS PipelineId,  'ContainerName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive  UNION

SELECT   11 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   11 AS PipelineId,  'SourceSubName' AS ParameterName,  'xxxx' AS ParameterValue,  1 AS IsActive UNION

SELECT   12 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   12 AS PipelineId,  'SourceSubName' AS ParameterName,  'YYYY' AS ParameterValue,  1 AS IsActive UNION 

SELECT   13 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   13 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION

SELECT   14 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   14 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive UNION 

SELECT   15 AS PipelineId,  'SourceName' AS ParameterName,  'RiskReg' AS ParameterValue,  1 AS IsActive UNION 
SELECT   15 AS PipelineId,  'SourceSubName' AS ParameterName,  'ZZZZ' AS ParameterValue,  1 AS IsActive 


)
MERGE	config.PipelineParameter	tgt
USING	PipelineParam				src	ON	tgt.PipelineId			= src.PipelineId
										AND	tgt.ParameterName		= src.ParameterName
WHEN	NOT MATCHED THEN
INSERT	(
		PipelineId
,		ParameterName
,		ParameterValue
,		IsActive
,		CreatedBy
,		CreatedDate
		)
VALUES	(
		RTRIM(src.PipelineId)
,		RTRIM(src.ParameterName)
,		RTRIM(src.ParameterValue)
,		RTRIM(src.IsActive)
,		SYSTEM_USER
,		GETUTCDATE()
		)
WHEN	MATCHED AND
		(
			ISNULL(src.ParameterName, '')		!= ISNULL(tgt.ParameterName, '')
		OR	ISNULL(src.ParameterValue, '')		!= ISNULL(tgt.ParameterValue, '')
		OR	src.IsActive						!= tgt.IsActive
		)
		THEN
UPDATE
SET		ParameterName		= src.ParameterName
,		ParameterValue		= src.ParameterValue
,		IsActive			= src.IsActive
,		UpdatedBy			= SYSTEM_USER
,		UpdatedDate			= GETUTCDATE();

		
