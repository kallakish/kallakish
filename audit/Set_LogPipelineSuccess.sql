/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Update pipeline log with a status of Success

**********************************************************************************************************************/
CREATE PROCEDURE [audit].Set_LogPipelineSuccess
(
	@CurrentExecutionId		UNIQUEIDENTIFIER
,	@StageId				SMALLINT
,	@PipelineId				INT
,	@ADFRunId		    	VARCHAR(50) = ''
)
AS

BEGIN TRY
	UPDATE	[audit].CurrentExecution
	SET		EndDateTime			= IIF(EndDateTime IS NULL, GETUTCDATE(), EndDateTime)
	,		PipelineStatus		        = 'Success'
	,		ADFRunId                        = @ADFRunId 
	WHERE	        CurrentExecutionId	        = @CurrentExecutionId
	AND		StageId				= @StageId
	AND		PipelineId			= @PipelineId;

	EXEC [audit].Insert_CurrentExecutionToHistorical @CurrentExecutionId, @StageId, @PipelineId, @ADFRunId;

END TRY

BEGIN CATCH
	THROW;
END CATCH

