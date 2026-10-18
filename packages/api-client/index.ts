import { StorefrontSpec, NlpExtractRequest, NlpExtractResponse } from "../schemas/entity_types";

export interface LayoutGenerateResponse {
  template_id: string;
  html: string;
}

export interface QaViolation {
  rule_id: string;
  viewport: number;
  message: string;
  severity: string;
}

export interface QaReport {
  passed: boolean;
  total_violations: number;
  repaired_count: number;
  violations: QaViolation[];
}

export interface QaRunResponse {
  status: string;
  qa_report: QaReport;
}

export class VoiceFrontClient {
  constructor(
    private asrUrl: string = "http://localhost:8001",
    private nlpUrl: string = "http://localhost:8002",
    private layoutUrl: string = "http://localhost:8003",
    private qaUrl: string = "http://localhost:8004"
  ) {}

  async extractMetadata(prompt: string, shopId?: string): Promise<NlpExtractResponse> {
    const res = await fetch(`${this.nlpUrl}/v1/nlp/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, shop_id: shopId }),
    });
    if (!res.ok) throw new Error(`NLP extraction failed: ${res.statusText}`);
    return res.json();
  }

  async generateLayout(spec: StorefrontSpec): Promise<LayoutGenerateResponse> {
    const res = await fetch(`${this.layoutUrl}/v1/layout/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(spec),
    });
    if (!res.ok) throw new Error(`Layout generation failed: ${res.statusText}`);
    return res.json();
  }

  async runQa(versionId: string): Promise<QaRunResponse> {
    const res = await fetch(`${this.qaUrl}/v1/qa/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version_id: versionId }),
    });
    if (!res.ok) throw new Error(`QA evaluation failed: ${res.statusText}`);
    return res.json();
  }
}
