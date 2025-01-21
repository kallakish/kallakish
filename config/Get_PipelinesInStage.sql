/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Return a list of stages to execute that already haven't
**********************************************************************************************************************/
CREATE PROCEDURE config.Get_PipelinesInStage
(
	@CurrentExecutionId	UNIQUEIDENTIFIER
,	@StageId			INT
,	@SetId				INT = 1
)
AS
BEGIN TRY
	SELECT	ce.PipelineId
	,		p.PipelineName
	FROM	[audit].CurrentExecution	ce
	JOIN	config.Pipeline				p	ON p.PipelineId = ce.PipelineId
	WHERE	ce.StageId						= @StageId
	AND		ce.SetId						= @SetId 	
	AND		ce.CurrentExecutionId			= @CurrentExecutionId
	AND		ISNULL(ce.PipelineStatus, '')	!= 'Success'
	order by p.ExecutionOrder asc;
END TRY

BEGIN CATCH
	THROW;
END CATCH