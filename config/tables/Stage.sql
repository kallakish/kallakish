CREATE TABLE config.Stage
(
	StageId				SMALLINT		NOT NULL	
,	StageName			VARCHAR(100)	NOT NULL
,	StageDescription	VARCHAR(200)	NOT NULL
,	ApplicationId		SMALLINT		NOT NULL
,	IsActive			BIT				NOT NULL	CONSTRAINT df_stgIsActive_Value		DEFAULT(1)
,	CreatedBy			VARCHAR(100)	NOT NULL	CONSTRAINT df_stgCreatedBy_Date		DEFAULT (SYSTEM_USER)
,	CreatedDate			DATETIME2(0)	NOT NULL	CONSTRAINT df_stgCreatedBy_User		DEFAULT (GETUTCDATE())
,	UpdatedBy			VARCHAR(100) 	NULL
,	UpdatedDate			DATETIME2(0)  	NULL

-- Keys
,	CONSTRAINT PK_Stage			PRIMARY KEY CLUSTERED (StageId)
,	CONSTRAINT FK_Stage_Process	FOREIGN KEY(ApplicationId)		REFERENCES config.[Application](ApplicationId)
);
GO
