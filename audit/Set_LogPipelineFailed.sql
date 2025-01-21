/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Update pipeline log with a status of Failed
				Persist rows over to HistoricalExcution
**********************************************************************************************************************/
CREATE PROCEDURE [audit].Set_LogPipelineFailed
(
	@CurrentExecutionId		UNIQUEIDENTIFIER
,	@StageId				SMALLINT
,	@PipelineId				INT
,	@ErrorMessage			NVARCHAR(1000)
,	@ADFRunId		    	VARCHAR(50)	= ''
)
AS

BEGIN TRY
	UPDATE	[audit].CurrentExecution
	SET		PipelineStatus		= 'Failed'
	,		ErrorMessage		= @ErrorMessage
	,	        ADFRunId		= @ADFRunId
	WHERE	        CurrentExecutionId	= @CurrentExecutionId
	AND		StageId		        = @StageId
	AND		PipelineId		= @PipelineId;

	EXEC [audit].Insert_CurrentExecutionToHistorical @CurrentExecutionId, @StageId, @PipelineId, @ADFRunId;
			
END TRY

BEGIN CATCH
	THROW;
END CATCH
