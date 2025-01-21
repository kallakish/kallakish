/**********************************************************************************************************************
Author:			Ray Betts               Date:			05/01/2021
initial version of the code
Change :        Kishore                 Date : 07/29/2021 
Added v2 code to the prameters generation
Description:	Return Parameters for Pipeline in JSON
				If GlobalExecutionType is F, then it will override whatever ExecutionType the Pipeline has set up
				
				SourceNameOverride - if it's anything but '', then concat to the existing source name. This will allow
									for testers to create test case container for loads e.g. avayatest01-analytics-cdr

				If startDate (yyyy-mm-dd) and endDate (yyyy-mm-dd) are supplied, these will be a manual override for date ranges either:
					startdate = 2021-07-01 and enddate '' - get everything after 1st July
					startdate = 2021-07-01 and enddate 2021-07-20 - get everything  1st July and 20th July
					startdate and enddate = '' - use lastmodifieddate from config.Pipeline
**********************************************************************************************************************/
CREATE PROCEDURE [config].[Get_PipelineParameters]
(
	@PipelineId 			INT
,	@GlobalExecutionType	CHAR(1)		= 'I'
,	@SourceNameOverride		VARCHAR(30)	= ''
,	@StartDate				VARCHAR(20) = ''
,	@EndDate				VARCHAR(20) = ''
,   @ExtraParams			VARCHAR(MAX) = ''
,   @Version                VARCHAR(20) = ''
,   @CurrentExecutionId     VARCHAR(36)
)
AS
BEGIN TRY
	DECLARE @JSON VARCHAR(MAX) = '',
			@LegacyVersion     VARCHAR(200) = '',
			@AppVersion VARCHAR(200) = '';
	DROP TABLE IF EXISTS #tempoverideparams;
	DROP TABLE IF EXISTS #tempparams;

	IF NOT EXISTS (
		SELECT 1
		FROM config.Pipeline
		WHERE PipelineId = @PipelineId
	)
	BEGIN
		RAISERROR('Requested pipeline id does not exist.', 16, 1);
		RETURN 404;
	END

		

	BEGIN
		--creating temp params table
        CREATE TABLE #tempparams (PipelineId varchar(2000),ParameterName varchar(2000),ParameterValue varchar(2000));
        INSERT INTO #tempparams SELECT @PipelineId as PipelineId,'' as ParameterName,'' as ParameterValue ;
       	
		--loading the overide parameters into temp table
		IF @ExtraParams = '' or @ExtraParams = '{}' or @ExtraParams is null
           
           INSERT INTO #tempparams 
           Select @PipelineId as PipelineId,
                    '""' as ParameterName,
                    '""' as ParameterValue ;
        ELSE 
        begin
            SELECT * INTO #tempoverideparams
			FROM OPENJSON(@ExtraParams);
            
		    INSERT INTO #tempparams
            SELECT 	@PipelineId as PipelineId,
                    CAST([key] AS VARCHAR) as ParameterName,
                    CAST([value] AS VARCHAR(2000)) as ParameterValue 
            from #tempoverideparams;
        end

		-- Set up dates if they are populated
		IF @StartDate is not null and @StartDate != '' SET @StartDate += ' 00:00:00';
		IF @EndDate is not null and @EndDate != ''  SET @EndDate += ' ' + CONVERT(VARCHAR, GETDATE(), 108);

		-- Start with PipelineId
		SELECT	@JSON	+=  '"PipelineId": "' + STRING_ESCAPE(CONVERT(VARCHAR, @PipelineId), 'json') + '",';
		
		-- Get Execution Type
		SELECT	@JSON	+= IIF(p.ExecutionType IS NULL
						, ''
						, '"ExecutionType": "' + STRING_ESCAPE(IIF(@GlobalExecutionType = 'F', @GlobalExecutionType, p.ExecutionType), 'json') + '",'
						)
		FROM	config.Pipeline			p	
		WHERE	p.PipelineId = @PipelineId;
		
		--Version from Params table

        SELECT  @AppVersion   +=  IIF(@Version != '',
			                         @Version ,
                                                IIF(
                                                    @SourceNameOverride != '', 
                                                    LOWER(@SourceNameOverride) + '-', 
                                                    ''
                                                ) + STRING_ESCAPE(CONVERT(VARCHAR, PP.ParameterValue), 'json')
        							) 			      
		FROM    config.Pipeline  p   
		INNER JOIN config.Stage  S  on p.StageId=S.StageId 
		INNER JOIN config.Application A on S.ApplicationId=A.ApplicationId
		LEFT JOIN config.PipelineParameter PP on p.PipelineId = PP.PipelineId and PP.ParameterName='Version'	
		WHERE   P.PipelineId = @PipelineId;

		-- Legacy Version from Params table

		SELECT  @LegacyVersion   = IIF(
						@SourceNameOverride != '', 
						LOWER(@SourceNameOverride) + '-',
						''
					) + STRING_ESCAPE(CONVERT(VARCHAR, PP.ParameterValue), 'json')
				FROM    config.Pipeline  p   
		INNER JOIN config.Stage  S  on p.StageId=S.StageId 
		INNER JOIN config.Application A on S.ApplicationId=A.ApplicationId
		LEFT JOIN config.PipelineParameter PP on p.PipelineId = PP.PipelineId and PP.ParameterName='LegacyVersion'	
		WHERE   P.PipelineId = @PipelineId;
		
		-- get core params from table
        WITH PipelineParam AS
        (
						SELECT  a.ParameterName,  a.PipelineId,  
						case a.ParameterName
						when 'SourceName' then  a.ParameterValue
						when 'EndDate'  then  IIF(@EndDate != '', STRING_ESCAPE(CONVERT(VARCHAR, @EndDate), 'json'), IIF(a.ParameterValue != '', a.ParameterValue, STRING_ESCAPE(FORMAT(GETDATE(), 'yyy-MM-dd HH:mm:ss'), 'json')))
						when 'LastModifiedDate'  then CONVERT(VARCHAR, IIF(ISNULL(@StartDate, '') = '', a.ParameterValue, @StartDate))
						when 'Version' then @AppVersion 
						when 'LegacyVersion' then @LegacyVersion
						else IIF(b.ParameterValue IS NULL, a.ParameterValue ,STRING_ESCAPE(CONVERT(VARCHAR(2000), b.ParameterValue), 'json')) END
						as ParameterValue
						FROM    config.PipelineParameter a
						left join #tempparams b on b.ParameterName=a.ParameterName collate SQL_Latin1_General_CP1_CI_AS
						WHERE   a.PipelineId = @PipelineId
						and a.IsActive = 1
        )
		SELECT	@JSON	+= IIF(ParameterValue IS NULL
							, ''
							, '"' + ParameterName + '": "' + STRING_ESCAPE(ParameterValue, 'json') + '",'
							)
		FROM	PipelineParam;

		-- Add last modified date (optional)
		-- Override with Startdate if it is supplied		
		IF (CHARINDEX('"LastModifiedDate":', @JSON, 0) = 0)
			SELECT	@JSON	+= IIF(p.LastModifiedDate IS NULL
											, ''
											, '"LastModifiedDate": "' + STRING_ESCAPE(CONVERT(VARCHAR, IIF(ISNULL(@StartDate, '') = '', p.LastModifiedDate, @StartDate)), 'json') + '",'
											)
			FROM	config.Pipeline			p	
			WHERE	p.PipelineId = @PipelineId;
		-- Add in end date for date range delta queries (optional)
		IF (CHARINDEX('"EndDate":', @JSON, 0) = 0)
				SELECT @JSON 	+= IIF(ISNULL(@EndDate, '') = ''
														, '"EndDate": "' + STRING_ESCAPE(FORMAT(GETDATE(), 'yyy-MM-dd HH:mm:ss'), 'json') + '",'
														, '"EndDate": "' + STRING_ESCAPE(CONVERT(VARCHAR, @EndDate), 'json') + '",'
														);
		
		--Add Version
		SELECT @JSON   +=IIF(
					A.Version IS NULL,
					'',
						IIF(PP.ParameterValue IS NULL, 
									IIF(@Version != '',
										'"Version": "' + @Version + '",',
											IIF(CHARINDEX('"Version":', @JSON) > 0,
												'', 
												'"Version": "' +IIF(
													@SourceNameOverride != '', 
													LOWER(@SourceNameOverride) + '-', 
													''
												) + STRING_ESCAPE(CONVERT(VARCHAR, A.Version), 'json') + '",'
											)
										),''
							)   
				)
		FROM config.Pipeline  p
			INNER JOIN config.Stage  S on p.StageId=S.StageId
			INNER JOIN config.Application A on S.ApplicationId=A.ApplicationId
			LEFT JOIN config.PipelineParameter PP on p.PipelineId = PP.PipelineId and PP.ParameterName='Version'
		WHERE   P.PipelineId = @PipelineId;

		-- Add Metadata
		SELECT	@JSON	+= IIF(p.Metadata IS NULL
						, ''
						, '"Metadata": "' + STRING_ESCAPE(CONVERT(VARCHAR, p.Metadata), 'json') + '",'
						)
		FROM    config.Pipeline         p
		WHERE   P.PipelineId = @PipelineId;

		-- Add currentExecutionId
		SELECT @JSON += ('"CurrentExecutionId": "' + @CurrentExecutionId + '",')
		FROM    config.Pipeline         p
		WHERE   P.PipelineId = @PipelineId;
		
		IF LEN(@JSON) > 0
		BEGIN
			--SET @JSON = '{"PipelineParameters":{' + LEFT(@JSON, LEN(@JSON) - 1) + '}}';
			SET @JSON = '{' + LEFT(@JSON, LEN(@JSON) - 1) + '}';

			UPDATE	[audit].CurrentExecution
			SET		PipelineParameterUsed = '{ ' + RIGHT(@Json, LEN(@JSON) - 1)
			WHERE	PipelineId = @PipelineId AND CurrentExecutionId = TRY_CONVERT(UNIQUEIDENTIFIER, @CurrentExecutionId);
		END
	END

	SELECT CONVERT(VARCHAR(MAX), @Json) AS PipelineParameters;

END TRY

BEGIN CATCH
	THROW;
END CATCH
GO
