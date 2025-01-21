/**********************************************************************************************************************
Author:			Ray Betts
Date:			05/01/2021
Description:	Update Pipeline Last Modified Date to store last load

**********************************************************************************************************************/
CREATE PROCEDURE config.Update_Pipeline_LastModifiedDate
(
	@PipelineId			INT
,	@LastModifiedDate	DATETIME2(0)
)
AS
BEGIN TRY
	UPDATE	config.Pipeline
	SET		LastModifiedDate		= @LastModifiedDate
	,		UpdatedDate				= GETUTCDATE()
	,		UpdatedBy				= SYSTEM_USER
	WHERE	PipelineId				= @PipelineId;
END TRY

BEGIN CATCH
	THROW;
END CATCH
