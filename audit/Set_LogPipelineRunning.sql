/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Update pipeline log with a status of running

**********************************************************************************************************************/
CREATE PROCEDURE [audit].Set_LogPipelineRunning
(
	@CurrentExecutionId		UNIQUEIDENTIFIER
,	@StageId				SMALLINT
,	@PipelineId				INT
)
AS

BEGIN TRY
	UPDATE	[audit].CurrentExecution
	SET		StartDateTime		= IIF(StartDateTime IS NULL, GETUTCDATE(), StartDateTime)
	,		PipelineStatus		= 'Running'
	WHERE	CurrentExecutionId	= @CurrentExecutionId
	AND		StageId				= @StageId
	AND		PipelineId			= @PipelineId;
END TRY

BEGIN CATCH
	THROW;
END CATCH