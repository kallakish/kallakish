CREATE TABLE config.PipelineGroup
(
	GroupId				SMALLINT		NOT NULL	
,	GroupName		    VARCHAR(200)	NOT NULL
,	Description			VARCHAR(200)	NOT NULL
,	[Order]		        SMALLINT		NOT NULL
,	IsActive			BIT				NOT NULL	CONSTRAINT df_GrpIsActive_Value		DEFAULT(1)
,	CreatedBy			VARCHAR(100)	NOT NULL	CONSTRAINT df_GrpCreatedBy_Date		DEFAULT (SYSTEM_USER)
,	CreatedDate			DATETIME2(0)	NOT NULL	CONSTRAINT df_GrpCreatedBy_User		DEFAULT (GETUTCDATE())
,	UpdatedBy			VARCHAR(100) 	NULL
,	UpdatedDate			DATETIME2(0)  	NULL

-- Keys
,	CONSTRAINT PK_Group			PRIMARY KEY CLUSTERED (GroupId)
);
GO