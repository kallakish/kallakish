/***************************************************
This Stored Procedure Combines Two JSON Strings
It Uses OPENJSON To Read Each String As A Table
Then Unions The Two Keeping Only Unique Keys
And Then Converts Back To JSON String Format.
***************************************************/
CREATE PROCEDURE [config].[Update_Pipeline_Metadata]
(
	@PipelineId     INT
,	@Metadata	    NVARCHAR(MAX)
)
AS
BEGIN TRY
    DECLARE @ExistingMetadata NVARCHAR(MAX);
    DECLARE @CombinedMetadata NVARCHAR(MAX);
    
    SET     @ExistingMetadata   = (SELECT ISNULL((SELECT Metadata FROM config.Pipeline WHERE PipelineId = @PipelineId), '{}'));

    SELECT  @CombinedMetadata   = COALESCE(@CombinedMetadata + ', ', '') + '"' + [key] + '":"' + value + '"'
        FROM 
        (SELECT [key], value FROM OPENJSON(@ExistingMetadata) WHERE [key] NOT IN (SELECT DISTINCT [key] FROM OPENJSON(@Metadata))
        UNION ALL
        SELECT [key], value FROM OPENJSON(@Metadata))
        AS Combined;

    SET @CombinedMetadata = '{' + @CombinedMetadata + '}'

	UPDATE	config.Pipeline
    SET		Metadata		        = @CombinedMetadata
	,		UpdatedDate				= GETUTCDATE()
	,		UpdatedBy				= SYSTEM_USER
	WHERE	PipelineId				= @PipelineId;
END TRY

BEGIN CATCH
	THROW;
END CATCH
