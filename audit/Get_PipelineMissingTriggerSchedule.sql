/**********************************************************************************************************************
Author:   Kishore Kalla
Date:   25-08-2022
Description: Return a list of pipelines which missed the schedule
**********************************************************************************************************************/
CREATE PROCEDURE audit.Get_PipelineMissingTriggerSchedule 
(@FromDate  DATETIME, 
@ToDate     DATETIME    ) AS 
BEGIN
   TRY 
   BEGIN
      WITH dates AS 
      (  SELECT @FromDate AS missedDate 
         UNION ALL
         SELECT DATEADD(day, 1, missedDate) as missedDate 
         FROM dates 
         WHERE DATEADD(day, 1, missedDate) <= @ToDate 
      )
      select
         t.TriggerId,
         t.PipelineId,
         p.PipelineName,
         p.PipelineDescription,
         t.TriggerType,
         t.UpdatedDate LastTriggeredTime,
         d.missedDate DateTriggerScheduleMissed
      from dates d,
           config.PipelineTrigger t 
         inner join config.Pipeline p on t.PipelineId = p.PipelineId 
      where CONVERT(DATE, ISNULL(t.LastSuccessfullExecution, '1900-01-01 00:00:00')) <> 
            CASE T.TriggerType WHEN 'S' THEN t.ActiveFrom 
            WHEN 'D' THEN CONVERT(DATE, ISNULL(d.missedDate, GETUTCDATE())) 
            WHEN 'W' THEN CASE WHEN DATEPART(weekday, ISNULL(d.missedDate, GETUTCDATE())) = t.FrequencyInterval THEN CONVERT(DATE, ISNULL(d.missedDate, GETUTCDATE())) END
            WHEN 'M' THEN CASE WHEN DAY(ISNULL(d.missedDate, GETUTCDATE())) = t.FrequencyInterval THEN CONVERT(DATE, ISNULL(d.missedDate, GETUTCDATE())) END
            ELSE CONVERT(DATE, ISNULL(d.missedDate, GETUTCDATE())) END
         and p.IsActive=1
         and NOT EXISTS 
         ( SELECT 'x' 
            FROM [audit].[HistoricalExecution] HX 
            WHERE HX.PipelineId = t.PipelineId 
            AND CONVERT(DATE, HX.StartDateTime) = CONVERT(DATE,d.missedDate)
         )
      order by t.PipelineId 
   END
END
TRY 
BEGIN
   CATCH THROW;
END
CATCH