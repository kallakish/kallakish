CREATE TABLE config.PipelineTrigger
(
    TriggerId                   INT             NOT NULL IDENTITY(1,1)
,   PipelineId                  INT             UNIQUE NOT NULL         -- At the moment only accepting 1 trigger per pipeline
,   TriggerType                 CHAR(1)         NOT NULL                -- (S) single execution, (D) daily execution, (W) weekly execution
,   FrequencyInterval           CHAR(2)         NOT NULL DEFAULT('0')   -- check https://docs.microsoft.com/en-us/sql/relational-databases/system-tables/dbo-sysschedules-transact-sql?redirectedfrom=MSDN&view=sql-server-ver15
,   IsActive			        BIT				NOT NULL CONSTRAINT df_triggerIsActive_Value DEFAULT(1)
,   ActiveFrom			        DATETIME2(0)  	NULL
,   LastSuccessfullExecution	DATETIME2(0)  	NULL
,   CreatedBy                   VARCHAR(100)    NOT NULL CONSTRAINT df_triggerCreatedBy_Date DEFAULT (SYSTEM_USER)
,   CreatedDate                 DATETIME2(0)    NOT NULL CONSTRAINT df_triggerCreatedBy_User DEFAULT (GETUTCDATE())
,   UpdatedBy                   VARCHAR(100)    NULL
,   UpdatedDate                 DATETIME2(0)    NULL
,   StartHour                   TINYINT         NOT NULL DEFAULT('1')
,   EndHour                     TINYINT         NULL

-- Keys
,   CONSTRAINT PK_PipelineTrigger       PRIMARY KEY CLUSTERED (TriggerId)
,   CONSTRAINT FK_PipeTrigger_Pipeline  FOREIGN KEY(PipelineId) REFERENCES config.Pipeline(PipelineId)
);
GO
