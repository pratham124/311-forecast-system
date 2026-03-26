export type IngestionRunAccepted = {
  runId: string;
  status: string;
};

export type IngestionRunStatus = {
  runId: string;
  status: string;
  resultType: string | null;
  startedAt: string;
  completedAt: string | null;
  cursorUsed: string | null;
  cursorAdvanced: boolean;
  candidateDatasetId: string | null;
  datasetVersionId: string | null;
  recordsReceived: number | null;
  failureReason: string | null;
};

export type CurrentDataset = {
  sourceName: string;
  datasetVersionId: string;
  updatedAt: string;
  updatedByRunId: string;
  recordCount: number;
  latestRequestedAt: string | null;
};
