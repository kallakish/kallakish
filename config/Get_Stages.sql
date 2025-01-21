/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Return a list of stages to execute that already haven't
**********************************************************************************************************************/
CREATE PROCEDURE config.Get_Stages
(
	@CurrentExecutionId	UNIQUEIDENTIFIER,
	@SetId INT = 1
)
AS
BEGIN TRY

--  Will fail the scheduled trigger pipeline when no pipelines run during that timeslot.
-- 	IF NOT EXISTS	(
-- 					SELECT	1
-- 					FROM	[audit].CurrentExecution
-- 					WHERE	ISNULL(PipelineStatus, '')	!= 'Success'
-- 					AND		CurrentExecutionId			= @CurrentExecutionId
-- 					AND		SetId						= @SetId
-- 					)
-- 	BEGIN
-- 		RAISERROR('Requested execution run does not contain any enabled stages/pipelines.', 16, 1);
-- 		RETURN 0;
-- 	END
--
-- 	ELSE
	BEGIN
		SELECT		ce.StageId
		,			ce.SetId
		,			a.SubscriptionId
		,			a.TenantId
		,			a.ResourceGroupName
		,			a.DataFactoryName
		FROM		[audit].CurrentExecution	ce
		JOIN		config.[Application]		a	ON	ce.ApplicationId	= a.ApplicationId
		WHERE		ISNULL(ce.PipelineStatus, '')	!= 'Success'
		AND			CurrentExecutionId				= @CurrentExecutionId
		AND			SetId							= @SetId
		GROUP BY	ce.StageId
		,			ce.SetId
		,			a.SubscriptionId
		,			a.TenantId
		,			a.ResourceGroupName
		,			a.DataFactoryName
		ORDER BY	ce.StageId ASC;
	END

END TRY

BEGIN CATCH
	THROW;
END CATCH
