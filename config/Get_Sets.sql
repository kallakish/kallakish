/**********************************************************************************************************************
Author:			Kishore Kalla
Date:			24/02/2022
Description:	Return a list of sets to execute that already haven't
**********************************************************************************************************************/
--drop procedure config.Get_Sets


CREATE PROCEDURE config.Get_Sets
(
	@CurrentExecutionId	UNIQUEIDENTIFIER
)
AS
BEGIN TRY

--  Will fail the scheduled trigger pipeline when no pipelines run during that timeslot.
-- 	IF NOT EXISTS	(
-- 					SELECT	1
-- 					FROM	[audit].CurrentExecution
-- 					WHERE	ISNULL(PipelineStatus, '')	!= 'Success'
-- 					AND		CurrentExecutionId			= @CurrentExecutionId
-- 					)
-- 	BEGIN
-- 		RAISERROR('Requested execution run does not contain any enabled stages/pipelines.', 16, 1);
-- 		RETURN 0;
-- 	END
--
-- 	ELSE
	BEGIN
		SELECT		ce.SetId
		,			ps.[Order]
		,			a.SubscriptionId
		,			a.TenantId
		,			a.ResourceGroupName
		,			a.DataFactoryName
		FROM		[audit].CurrentExecution	ce
		JOIN		config.[Application]		a	ON	ce.ApplicationId	= a.ApplicationId
		Left join   config.PipelineSet			ps	on	ce.SetId			= ps.SetId	
		WHERE		ISNULL(ce.PipelineStatus, '')	!= 'Success'
		AND			CurrentExecutionId				= @CurrentExecutionId
		GROUP BY	ce.SetId
		,			ps.[Order]
		,			a.SubscriptionId
		,			a.TenantId
		,			a.ResourceGroupName
		,			a.DataFactoryName
		ORDER BY	ps.[Order] ASC;
	END

END TRY

BEGIN CATCH
	THROW;
END CATCH
