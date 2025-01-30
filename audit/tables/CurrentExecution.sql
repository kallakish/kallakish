CREATE TABLE [audit].CurrentExecution
(
	CurrentExecutionId		UNIQUEIDENTIFIER	        NOT NULL	
,	ApplicationId			SMALLINT		       	NOT NULL
,	StageId				SMALLINT			NOT NULL
,	SetId				    INT			NOT NULL	DEFAULT(1)
,	PipelineId			    INT			NOT NULL
,	CreatedDateTime		DATETIME2(0)		NULL	
,	StartDateTime			DATETIME2(0)		        NULL		
,	PipelineStatus			VARCHAR(50)			NULL
,	EndDateTime			DATETIME2(0)			NULL
,	RowsRead			INT				NULL
,	RowsCopied			INT				NULL
,	PipelineParameterUsed	        NVARCHAR(MAX)			NULL  
,	ErrorMessage			NVARCHAR(1000)			NULL
,	ADFRunId                        VARCHAR (50)        		NULL
-- PK's
,	CONSTRAINT PK_CurrentExecution				PRIMARY KEY CLUSTERED (CurrentExecutionId, ApplicationId, StageId, PipelineId)
);
GO
