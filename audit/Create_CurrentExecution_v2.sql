/**********************************************************************************************************************
Description:	Check if Stage exists for App
					- Raise Error
					- Insert empty steps
				Optional execution if PipelineId is anything but -1
				and the same again for StageId
**********************************************************************************************************************/

CREATE PROCEDURE [audit].Create_CurrentExecution_v2
(
	@ApplicationId		SMALLINT		
,	@CurrentExecutionId	UNIQUEIDENTIFIER 	= NULL
,	@PipelineId			INT					= -1
,	@StageId			INT					= -1
,	@SetId				INT					= -1
,   @GroupId            INT                 = -1
,   @StartHour          TINYINT             = 255
,   @IgnoreSchedule     BIT                 = 0
)
AS
BEGIN TRY
-- We are running every hour now so this will return a failed pipeline if no pipelines are in the timeslot.
-- IF NOT EXISTS       (
--                     SELECT	1
--                     FROM        config.Stage            s
--                     JOIN        config.Pipeline         p   ON p.StageId = s.StageId
--                     LEFT JOIN   config.PipelineSet      ps  ON p.SetId = ps.SetId
--                     LEFT JOIN   config.PipelineTrigger  t   ON p.PipelineId = t.PipelineId
--                     WHERE   ApplicationId        = @ApplicationId
--                     AND	   (	@PipelineId     = -1
--                             OR	p.PipelineId    = @PipelineId
--                             )
--                     AND	   (	@StageId        = -1
--                             OR	s.StageId       = @StageId
--                             )
--                     AND     (	@SetId          = -1
--                             OR	ps.SetId        = @SetId
--                             )
--                     AND     (	@GroupId 		= -1
--                             OR   ps.GroupId      = @GroupId
--                             )
--                     AND	   s.IsActive          = 1
--                     AND	   ps.IsActive         = 1
--                     AND	   (   p.IsActive      = 1
--                             OR  p.PipelineId    = @PipelineId
--                             )
--                     AND     (   @StartHour      = 255
--                             OR  t.StartHour     = @StartHour
--                             OR  (t.StartHour IS NULL AND @StartHour = 1)
--                             )
--                     )
-- BEGIN
--     RAISERROR('Requested execution run does not contain any enabled stages/pipelines.', 16, 1);
-- RETURN 0;
-- END
--
-- ELSE
    BEGIN
        EXEC [audit].Cancel_Timeout_Pipelines;

        SET @CurrentExecutionId = NEWID();

        -- Get new entries to insert
        CREATE TABLE #newCurrentExecutionEntries (
            CurrentExecutionId UNIQUEIDENTIFIER, 
            ApplicationId SMALLINT, 
            StageId SMALLINT, 
            SetId INT, 
            PipelineId INT, 
            CreatedDateTime DATETIME2(0),
        );
        INSERT INTO #newCurrentExecutionEntries
        SELECT	@CurrentExecutionId
            ,      s.ApplicationId
            ,      s.StageId
            ,      ps.SetId
            ,      p.PipelineId
            ,      GETUTCDATE() as CreatedDateTime
        FROM    config.Stage    s
            JOIN        config.Pipeline         p   ON p.StageId = s.StageId
            LEFT JOIN   config.PipelineSet      ps  ON ps.SetId = p.SetId
            LEFT JOIN   config.PipelineTrigger  t   ON p.PipelineId = t.PipelineId
        WHERE   s.ApplicationId	= @ApplicationId
            AND (   @PipelineId     = -1
                OR  p.PipelineId    = @PipelineId
            )
            AND (   @StageId        = -1
                OR  s.StageId       = @StageId
            )
            AND (   @SetId          = -1
                OR  ps.SetId        = @SetId
            )
            AND	(   @GroupId        = -1
                OR  ps.GroupId      = @GroupId
            )
            AND     s.IsActive      = 1
            AND     ps.IsActive     = 1
            AND (   p.IsActive      = 1
                OR  p.PipelineId    = @PipelineId
            )
            AND (   
                @IgnoreSchedule = 1
                OR  (   @StartHour  = 255
                    OR  t.StartHour     = @StartHour
                    OR  (t.StartHour IS NULL AND @StartHour = 1) -- Defaults all unscheduled pipelines to run as part of the 1am UTC trigger.
                    )
                    -- Validate schedule
                    AND (t.ActiveFrom IS NULL OR (CONVERT(date, t.ActiveFrom)<= CONVERT(date, GETUTCDATE()) ))
                    AND (
                      CONVERT(date, ISNULL(t.LastSuccessfullExecution, '1900-01-01 00:00:00')) <=
                          CASE T.TriggerType
                              WHEN 'S' THEN t.ActiveFrom
                              WHEN 'D' THEN  CONVERT(date, GETUTCDATE())
                              WHEN 'W' THEN  CASE WHEN DATEPART(weekday,  GETUTCDATE()) = t.FrequencyInterval THEN  CONVERT(date, GETUTCDATE()) END
                              WHEN 'M' THEN  CASE WHEN DAY(GETUTCDATE()) = t.FrequencyInterval THEN  CONVERT(date, GETUTCDATE()) END
                              ELSE    CONVERT(date, GETUTCDATE())
                          END
                      OR p.PipelineId = @PipelineId
                    )
            )
       
        -- Check if any of the pipelines are locked
        CREATE TABLE #lockedPipelines (
            PipelineId INT
        );
        INSERT INTO #lockedPipelines
        SELECT nce.PipelineId
        FROM #newCurrentExecutionEntries nce INNER JOIN [audit].CurrentExecution ce ON nce.PipelineId = ce.PipelineId
        INNER JOIN [config].Pipeline cp ON nce.PipelineId = cp.PipelineId
        WHERE cp.AllowParallelExecution = 0;

        DECLARE @numLockedPipelines INT = (
            SELECT COUNT(*)
            FROM #lockedPipelines
        )
        IF @numLockedPipelines > 0 BEGIN
            DECLARE @errorMessage NVARCHAR(MAX)
            SELECT @errorMessage = (
                SELECT CONCAT('Some pipelines are already running: [', locked.pipelineIdList, ']') AS error
                FROM
                (
                    SELECT STRING_AGG(CONVERT(VARCHAR(20), PipelineId), ',') AS pipelineIdList
                    FROM #lockedPipelines
                ) AS locked
            );
            THROW 50001, @errorMessage, 1;
        END
        
        -- Insert new entries
        INSERT	[audit].CurrentExecution
        (
                CurrentExecutionId
        ,       ApplicationId
        ,       StageId
        ,       SetId
        ,       PipelineId
        ,       CreatedDateTime
        )
        SELECT * FROM #newCurrentExecutionEntries;

        SELECT @CurrentExecutionId AS CurrentExecutionId;
    END

END TRY

BEGIN CATCH
    THROW;
END CATCH