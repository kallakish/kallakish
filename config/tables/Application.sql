CREATE TABLE config.[Application]
(
	ApplicationId			SMALLINT 				NOT NULL		
,	ApplicationName			VARCHAR(100)			NOT NULL
,	ApplicationDescription	VARCHAR(200)			NULL
,	SubscriptionId			NVARCHAR(100)			NULL
,	TenantId				NVARCHAR(100)			NULL
,	ResourceGroupName		NVARCHAR(200)			NULL
,	DataFactoryName			NVARCHAR(200)			NULL
,	[Version]				NVARCHAR(10)			NULL
,	IsActive				BIT						NULL		CONSTRAINT df_appIsActive_Value	DEFAULT(1)
,	CreatedBy				VARCHAR(100)			NOT NULL	CONSTRAINT df_appCreatedBy_Date	DEFAULT(GETUTCDATE())
,	CreatedDate				DATETIME2(0)			NOT NULL	CONSTRAINT df_appCreatedBy_User	DEFAULT(SYSTEM_USER)	
,	UpdatedBy				VARCHAR(100)			NULL			
,	UpdatedDate				DATETIME2(0)			NULL			

-- PK
,	CONSTRAINT PK_Application PRIMARY KEY CLUSTERED (ApplicationId)
);
GO
