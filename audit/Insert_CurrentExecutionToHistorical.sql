
/**********************************************************************************************************************
Author:			Ray Betts
Date:			15/07/2021
Description:	Insert rows from Current Execution to Historical
**********************************************************************************************************************/
CREATE PROCEDURE [audit].Insert_CurrentExecutionToHistorical
(
	@CurrentExecutionId		UNIQUEIDENTIFIER
,	@StageId				SMALLINT
,	@PipelineId				INT
,	@ADFRunId		    	VARCHAR(50)	= ''
)
AS

BEGIN TRY
	INSERT	[audit].HistoricalExecution
	(
			CurrentExecutionId
	,		ApplicationId
	,		StageId	
	,		SetId			
	,		PipelineId	
	,		ADFRunId		
	,		StartDateTime		
	,		PipelineStatus		
	,		EndDateTime	
	,		RowsRead
	,		RowsCopied
	,		PipelineParameterUsed
	,		ErrorMessage
	,		CreatedDateTime
	)
	SELECT	CurrentExecutionId
	,		ApplicationId		
	,		StageId	
	,		SetId	
	,		PipelineId	
	,		ADFRunId				
	,		StartDateTime		
	,		PipelineStatus		
	,		EndDateTime
	,		RowsRead
	,		RowsCopied
	,		PipelineParameterUsed
	,	 	ErrorMessage
 	,		CreatedDateTime
	FROM		[audit].CurrentExecution
	WHERE	  (CurrentExecutionId  = @CurrentExecutionId OR @CurrentExecutionId  is NULL)
	AND		  (PipelineId					 = @PipelineId OR @PipelineId = -1)
	AND		  (StageId						 = @StageId OR @StageId = -1)
	AND	 	  (PipelineStatus	   	 = 'Failed' OR PipelineStatus = 'Success');
		
	DELETE FROM [audit].CurrentExecution 	
	WHERE   (CurrentExecutionId  = @CurrentExecutionId OR @CurrentExecutionId  is NULL)
	AND		  (PipelineId					 = @PipelineId OR @PipelineId = -1)
	AND		  (StageId						 = @StageId OR @StageId = -1)
	AND	 	  (PipelineStatus	   	 = 'Failed' OR PipelineStatus = 'Success');

END TRY
BEGIN CATCH
	THROW;
END CATCH
