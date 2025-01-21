CREATE PROCEDURE [audit].Cancel_Timeout_Pipelines
AS
BEGIN TRY
  UPDATE	[audit].CurrentExecution
  SET  PipelineStatus   = 'Failed'
  ,    ErrorMessage     = 'Pipeline timeout'
  ,    EndDateTime      = IIF(EndDateTime IS NULL, GETUTCDATE(), EndDateTime)
  WHERE CreatedDateTime   < DATEADD(DD,-1, GETUTCDATE());

  EXEC [audit].Insert_CurrentExecutionToHistorical @CurrentExecutionId=NULL, @StageId=-1, @PipelineId=-1;
			
END TRY

BEGIN CATCH
	THROW;
END CATCH
