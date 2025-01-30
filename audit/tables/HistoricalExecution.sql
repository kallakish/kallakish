CREATE TABLE [audit].HistoricalExecution
(
	HistoricalExecutionId	INT			NOT NULL	IDENTITY(1,1)
,	CurrentExecutionId	UNIQUEIDENTIFIER	NOT NULL
,	ApplicationId		SMALLINT		NOT NULL
,	StageId			SMALLINT		NOT NULL
,	SetId			     INT		NOT NULL	DEFAULT(1)
,	PipelineId		     INT		NOT NULL
,	CreatedDateTime		DATETIME2(0)		NULL	
,	StartDateTime		DATETIME2(0)		NULL	
,	PipelineStatus		VARCHAR(50)		NULL
,	EndDateTime		DATETIME2(0)		NULL
,	RowsRead		INT			NULL
,	RowsCopied		INT			NULL
,	PipelineParameterUsed	NVARCHAR(MAX)		NULL		CONSTRAINT df_hisexeParam	DEFAULT('none')
,	ErrorMessage		NVARCHAR(1000)		NULL
,	ADFRunId                VARCHAR (50)            NULL

-- PK's
,	CONSTRAINT PK_HistoricalExecution				PRIMARY KEY CLUSTERED (HistoricalExecutionId)
);
GO
