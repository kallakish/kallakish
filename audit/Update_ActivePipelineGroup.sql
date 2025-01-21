CREATE PROCEDURE [audit].Update_ActivePipelineGroup
(
    @GroupId INT,
    @IsActive INT = 1
)
AS
BEGIN TRY

    UPDATE config.PipelineGroup
    SET IsActive = @IsActive
    WHERE GroupId = @GroupId

    UPDATE config.PipelineSet
    SET isactive = @IsActive
    WHERE GroupId = @GroupId

    UPDATE p
    SET isactive = @IsActive
    FROM config.Pipeline p
    INNER JOIN config.PipelineSet ps ON p.SetId = ps.SetId
    INNER JOIN config.PipelineGroup pg ON ps.GroupId= pg.GroupId
    WHERE pg.GroupId=@GroupId

END TRY

BEGIN CATCH
	THROW;
END CATCH

