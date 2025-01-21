-- Add in initial Applications

DECLARE @environment	VARCHAR(100) = '$(environment)'
,		@SubscriptionId	VARCHAR(50) = '$(SubscriptionId)'
,		@TenantId		VARCHAR(50) = '$(TenantId)'
,		@AppVersion		VARCHAR(3)	= '$(Version)';

WITH Apps AS
(
SELECT	1										AS ApplicationId
,		'SRP'									AS ApplicationName
,		'Strategic Reporting Platform'				AS ApplicationDescription
,		@SubscriptionId							AS SubscriptionId
,		@TenantId								AS TenantId
,		'srp-' + @environment + '-rg'			AS ResourceGroupName
,		'srp-synapse-' + @environment 			AS DataFactoryName
,		@AppVersion								AS [Version]
,		1										AS IsActive
)
MERGE	config.[Application]	tgt
USING	Apps					src	ON	tgt.ApplicationId		= src.ApplicationId
WHEN	NOT MATCHED THEN
INSERT	(
		ApplicationId
,		ApplicationName
,		ApplicationDescription
,		SubscriptionId
,		TenantId
,		ResourceGroupName
,		DataFactoryName
,		[Version]
,		IsActive
,		CreatedBy
,		CreatedDate
		)
VALUES	(
		src.ApplicationId
,		src.ApplicationName
,		src.ApplicationDescription
,		src.SubscriptionId
,		src.TenantId
,		src.ResourceGroupName
,		src.DataFactoryName
,		src.[Version]
,		src.IsActive
,		SYSTEM_USER
,		GETUTCDATE()
		)
WHEN	MATCHED AND
		(
			ISNULL(src.ApplicationName, '')			!= ISNULL(tgt.ApplicationName, '')
		OR	ISNULL(src.ApplicationDescription, '')	!= ISNULL(tgt.ApplicationDescription, '')
		OR	ISNULL(src.SubscriptionId, 0x0)			!= ISNULL(tgt.SubscriptionId, 0x0)
		OR	ISNULL(src.TenantId, 0x0)				!= ISNULL(tgt.TenantId, 0x0)
		OR	ISNULL(src.ResourceGroupName, '')		!= ISNULL(tgt.ResourceGroupName, '')
		OR	ISNULL(src.DataFactoryName, '')			!= ISNULL(tgt.DataFactoryName, '')
		OR	ISNULL(src.[Version], '')				!= ISNULL(tgt.[Version], '')
		OR	src.IsActive							!= tgt.IsActive
		)
		THEN
UPDATE
SET		ApplicationName			= src.ApplicationName
,		ApplicationDescription	= src.ApplicationDescription
,		SubscriptionId			= src.SubscriptionId
,		TenantId				= src.TenantId
,		ResourceGroupName		= src.ResourceGroupName
,		DataFactoryName			= src.DataFactoryName
,		[Version]				= src.[Version]			
,		IsActive				= src.IsActive
,		UpdatedBy				= SYSTEM_USER
,		UpdatedDate				= GETUTCDATE()
WHEN 	NOT MATCHED BY SOURCE THEN
UPDATE	
SET		IsActive = 0;	
		