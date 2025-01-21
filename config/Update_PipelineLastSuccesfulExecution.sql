CREATE PROCEDURE config.Create_Or_Update_Trigger_LastSuccessfulExecution
(
	@PipelineId			INT
,	@LastSuccessfullExecution	DATETIME2(0)
)
AS
BEGIN TRY

	IF NOT EXISTS (SELECT 1 FROM config.PipelineTrigger WHERE PipelineId = @PipelineId)
	BEGIN
		INSERT	into config.PipelineTrigger (
				PipelineId
		,		TriggerType
		,		ActiveFrom
		,		IsActive
		,		CreatedBy
		,		CreatedDate
		,		UpdatedBy
		,		UpdatedDate
		,		LastSuccessfullExecution
				)
		VALUES	(
				RTRIM(@PipelineId)
		,		RTRIM('D')
		,		RTRIM(GETUTCDATE())
		,		RTRIM(1)
		,		SYSTEM_USER
		,		GETUTCDATE()
		,		SYSTEM_USER
		,		GETUTCDATE()
		,		@LastSuccessfullExecution
				)
	END
	ELSE
	BEGIN
			UPDATE	config.PipelineTrigger
			SET		LastSuccessfullExecution		= @LastSuccessfullExecution
			,		UpdatedDate				= GETUTCDATE()
			,		UpdatedBy				= SYSTEM_USER
			WHERE	PipelineId				= @PipelineId;
	END
END TRY

BEGIN CATCH
	THROW;
END CATCH
