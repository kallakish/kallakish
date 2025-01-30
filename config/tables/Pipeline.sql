CREATE TABLE config.Pipeline
(
    PipelineId             INT              NOT NULL
,   PipelineName           VARCHAR(100)     NOT NULL
,   PipelineDescription    VARCHAR(200)     NOT NULL
,   SetId                  INT              NOT NULL    CONSTRAINT df_pipeSetId_Value       DEFAULT(1)
,   StageId                SMALLINT         NOT NULL
,   ExecutionOrder         SMALLINT         NOT NULL    CONSTRAINT df_pipeExecOrd_Value     DEFAULT(10)
,   ExecutionType          CHAR(1)          NOT NULL    CONSTRAINT df_pipeExecType_Value    DEFAULT('I') -- I or F
,   LastModifiedDate       DATETIME2(0)     NOT NULL    CONSTRAINT df_pipeDate_Value        DEFAULT('1900-01-01')
,   IsActive               BIT              NOT NULL    CONSTRAINT df_pipeIsActive_Value    DEFAULT(1)
,   CreatedBy              VARCHAR(100)     NOT NULL    CONSTRAINT df_pipeCreatedBy_Date    DEFAULT (SYSTEM_USER)
,   CreatedDate            DATETIME2(0)     NOT NULL    CONSTRAINT df_pipeCreatedBy_User    DEFAULT (GETUTCDATE())
,   UpdatedBy              VARCHAR(100)     NULL
,   UpdatedDate            DATETIME2(0)     NULL
,   Metadata               NVARCHAR(MAX)    NULL
,   AllowParallelExecution BIT              NOT NULL                                        DEFAULT(0)

-- Keys
,   CONSTRAINT PK_Pipeline           PRIMARY KEY CLUSTERED (PipelineId)
,   CONSTRAINT FK_Pipleline_Stage    FOREIGN KEY(StageId) REFERENCES config.Stage(StageId)
,   CONSTRAINT FK_Pipleline_Set    FOREIGN KEY(SetId) REFERENCES config.PipelineSet(SetId)
);
GO