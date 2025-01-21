/**********************************************************************************************************************
Author:			Ray Betts
Date:			08/01/2021
Description:	Get last modified from pipeline

**********************************************************************************************************************/
CREATE PROCEDURE config.Get_Pipeline_LastModifiedDate
(
	@PipelineId	INT
)
AS
BEGIN TRY

	SELECT	LastModifiedDate  
	FROM	config.Pipeline 
	WHERE	PipelineId = @PipelineId;

END TRY

BEGIN CATCH
	THROW;
END CATCH
