-- PCQ weelky pipeline trigger

WITH PipelineTrigger AS
(
	SELECT   1 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
	UNION SELECT   2 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
	UNION SELECT   3 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
 	UNION SELECT   4 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
  UNION SELECT   5 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour

  UNION SELECT   6 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
  UNION SELECT   7 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
	UNION SELECT   8 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
 	UNION SELECT   9 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
  UNION SELECT   10 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour

  UNION SELECT   11 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
  UNION SELECT   12 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
	UNION SELECT   13 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
 	UNION SELECT   14 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
  UNION SELECT   15 AS PipelineId,  'D' AS TriggerType,  '0' AS FrequencyInterval,  1 AS IsActive, '2021-12-01 00:00:00' AS  ActiveFrom, 0 as StartHour
)
MERGE	config.PipelineTrigger	trg
USING	PipelineTrigger			src	ON	trg.PipelineId			= src.PipelineId
WHEN	NOT MATCHED THEN
INSERT	(
		PipelineId
,		TriggerType
,		FrequencyInterval
,		IsActive
,		ActiveFrom
,		CreatedBy
,		CreatedDate
,		StartHour
		)
VALUES	(
		src.PipelineId
,		src.TriggerType
,		src.FrequencyInterval
,		src.IsActive
,		src.ActiveFrom
,		SYSTEM_USER
,		GETUTCDATE()
,		src.StartHour
		)
WHEN	MATCHED AND
		(
			ISNULL(src.TriggerType, '')		!= ISNULL(trg.TriggerType, '')
		OR	ISNULL(src.FrequencyInterval, '')		!= ISNULL(trg.FrequencyInterval, '')
		OR	ISNULL(src.ActiveFrom, '')		!= ISNULL(trg.ActiveFrom, '')
		OR	src.IsActive						!= trg.IsActive
    OR	src.StartHour						!= trg.StartHour
		)
		THEN
UPDATE
SET		TriggerType		= src.TriggerType
,		FrequencyInterval		= src.FrequencyInterval
,		ActiveFrom		= src.ActiveFrom
,		IsActive			= src.IsActive
,		StartHour			= src.StartHour
,		UpdatedBy			= SYSTEM_USER
,		UpdatedDate			= GETUTCDATE();

		
