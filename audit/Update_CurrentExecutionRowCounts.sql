/**********************************************************************************************************************
Author:			Ray Betts
Date:			20/07/2021
Description:	Update RowCounts - RecordsRead and RowsCopied into CurrentExection by PipelineId and CurrentExecutionId

**********************************************************************************************************************/
CREATE PROCEDURE [audit].Update_CurrentExecutionRowCounts
(
	@PipelineId			INT
,	@RowsRead			INT
,	@RowsCopied			INT
,	@CurrentExecutionId	VARCHAR(36)
)
AS
BEGIN TRY

    UPDATE	[audit].CurrentExecution
    SET   RowsRead   = isnull(RowsRead,0) + isnull(@RowsRead,0)
    ,     RowsCopied = isnull(RowsCopied,0) + isnull(@RowsCopied,0)
    WHERE PipelineId = @PipelineId AND CurrentExecutionId = TRY_CONVERT(UNIQUEIDENTIFIER, @CurrentExecutionId);

END TRY

BEGIN CATCH
    THROW;
END CATCH
