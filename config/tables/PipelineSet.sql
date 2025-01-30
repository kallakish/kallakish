CREATE TABLE config.PipelineSet
(
	SetId				INT             NOT NULL	
,	Description			VARCHAR(200)	NOT NULL
,	GroupId	            SMALLINT	    NOT NULL	DEFAULT(1)
,	[Order]		        SMALLINT		NOT NULL
,	IsActive			BIT				NOT NULL	CONSTRAINT df_setIsActive_Value		DEFAULT(1)
,	CreatedBy			VARCHAR(100)	NOT NULL	CONSTRAINT df_setCreatedBy_Date		DEFAULT (SYSTEM_USER)
,	CreatedDate			DATETIME2(0)	NOT NULL	CONSTRAINT df_setCreatedBy_User		DEFAULT (GETUTCDATE())
,	UpdatedBy			VARCHAR(100) 	NULL
,	UpdatedDate			DATETIME2(0)  	NULL

-- Keys
,	CONSTRAINT PK_Set			PRIMARY KEY CLUSTERED (SetId)
,	CONSTRAINT FK_Set_Group		FOREIGN KEY(GroupId)		REFERENCES config.PipelineGroup(GroupId)
);
GO