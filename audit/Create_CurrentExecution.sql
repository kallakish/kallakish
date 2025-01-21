/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Check if Stage exists for App
					- Raise Error
					- Truncate Table
					- Insert empty steps
				Optional execution if PipelineId is anything but -1
				and the same again for StageId

DEPRECATED
**********************************************************************************************************************/
CREATE PROCEDURE [audit].Create_CurrentExecution
(
	@ApplicationId		SMALLINT		
,	@CurrentExecutionId	UNIQUEIDENTIFIER 	= NULL
,	@PipelineId			INT					= -1
,	@StageId			INT					= -1
)
AS
BEGIN TRY

		IF NOT EXISTS	(
						SELECT	1
						FROM	config.Stage	s
						JOIN	config.Pipeline	p	ON p.StageId = s.StageId
						WHERE	ApplicationId		= @ApplicationId
						AND		(	@PipelineId 	= -1
								OR	p.PipelineId	= @PipelineId
								)
					    AND		(	@StageId 		= -1
								OR	s.StageId		= @StageId
								)
						AND		s.IsActive			= 1
						AND		(p.IsActive= 1 OR p.PipelineId = @PipelineId)
						)
		BEGIN
			RAISERROR('Requested execution run does not contain any enabled stages/pipelines.', 16, 1);
			RETURN 0;
		END

		ELSE
		BEGIN

		SET @CurrentExecutionId = NEWID();

			INSERT	[audit].CurrentExecution
			(
					CurrentExecutionId
			,		ApplicationId		
			,		StageId				
			,		PipelineId					
			)
			SELECT	@CurrentExecutionId
			,		s.ApplicationId
			,		s.StageId
			,		p.PipelineId
			FROM	config.Stage	s
			JOIN	config.Pipeline	p	ON p.StageId = s.StageId
			WHERE	s.ApplicationId	= @ApplicationId
			AND		(	@PipelineId 	= -1
					OR	p.PipelineId	= @PipelineId
					)
            AND		(	@StageId 		= -1
					OR	s.StageId		= @StageId
					)					
			AND		s.IsActive			= 1
			AND		(p.IsActive= 1 OR p.PipelineId = @PipelineId);

			SELECT @CurrentExecutionId AS CurrentExecutionId;
		END

END TRY

BEGIN CATCH
	THROW;
END CATCH