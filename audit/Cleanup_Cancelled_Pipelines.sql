CREATE PROCEDURE [audit].Cleanup_Cancelled_Pipelines
(
    @PipelineIdStart INT,
    @PipelineIdEnd   INT
)
AS
BEGIN TRY
    --Mark the pipelines as cancelled
    UPDATE [audit].CurrentExecution
    SET PipelineStatus = 'Failed',
        ErrorMessage = 'Pipeline timeout'
    WHERE SetId BETWEEN @PipelineIdStart AND @PipelineIdEnd
    
    --Migrate to the historical execution table
    DECLARE @Cursor CURSOR;
    DECLARE @cid UNIQUEIDENTIFIER;
    DECLARE @StageId SMALLINT;
    DECLARE @PipelineId INT;
    BEGIN
        CREATE TABLE #toCancel(
            CurrentExecutionId UNIQUEIDENTIFIER,
            StageId INT,
            PipelineId INT
        )
        INSERT INTO #toCancel
            SELECT CurrentExecutionId, StageId, PipelineId 
            FROM [audit].CurrentExecution
            WHERE PipelineId BETWEEN @PipelineIdStart AND @PipelineIdEnd

        SET @Cursor = CURSOR FOR
            SELECT * FROM #toCancel
        OPEN @Cursor
        FETCH NEXT FROM @Cursor
        INTO @cid, @StageId, @PipelineId

        WHILE @@FETCH_STATUS = 0
        BEGIN
            EXEC [audit].Insert_CurrentExecutionToHistorical @CurrentExecutionId = @cid, @StageId = @StageId, @PipelineId = @PipelineId
            FETCH NEXT FROM @Cursor
            INTO @cid, @StageId, @PipelineId
        END;


        CLOSE @Cursor;
        DEALLOCATE @Cursor;

        --show results to confirm they are correct
        SELECT DISTINCT [audit].HistoricalExecution.*
        FROM [audit].HistoricalExecution
        INNER JOIN #toCancel ON [audit].HistoricalExecution.CurrentExecutionId = #toCancel.CurrentExecutionId
    END;

END TRY

BEGIN CATCH
	THROW;
END CATCH