CREATE TABLE config.PipelineParameter
(
	PipelineParameterId INT             NOT NULL    IDENTITY(1,1)
,	PipelineId          INT             NOT NULL
,	ParameterName       VARCHAR(200)    NOT NULL
,	ParameterValue      VARCHAR(MAX)    NOT NULL
,	IsActive            BIT             NOT NULL    CONSTRAINT df_pipeparIsActive_Value    DEFAULT(1)
,	CreatedBy           VARCHAR(100)    NOT NULL    CONSTRAINT df_pipeparCreatedBy_Date    DEFAULT (SYSTEM_USER)
,	CreatedDate         DATETIME2(0)    NOT NULL    CONSTRAINT df_pipeparCreatedBy_User    DEFAULT (GETUTCDATE())
,	UpdatedBy           VARCHAR(100)    NULL
,	UpdatedDate         DATETIME2(0)    NULL

-- Keys
,	CONSTRAINT PK_PipelineParam			PRIMARY KEY CLUSTERED (PipelineParameterId)
,	CONSTRAINT FK_PipeParam_Pipeline	FOREIGN KEY(PipelineId)		REFERENCES config.Pipeline(PipelineId)
);
GO