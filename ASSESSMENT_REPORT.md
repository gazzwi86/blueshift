# PixieOps Harness Assessment Report

**Date**: 2025-12-19
**Assessor**: Claude Code
**Status**: ISSUES FOUND - Remediation Required

---

## Executive Summary

The project shows good structural progress with proper IaC patterns, but has **critical data pipeline failures** that mean the agent is not actually processing real data. The features marked as "passing" do not reflect the true operational state.

---

## Assessment Findings

### 1. Infrastructure as Code (IaC)

| Check | Status | Notes |
|-------|--------|-------|
| Terraform state managed | PASS | 78+ resources in state |
| Knowledge Base via IaC | PASS | Uses null_resource + AWS CLI (valid pattern for S3 Vectors) |
| No hardcoded manual IDs | PASS | KB ID captured from IaC execution |
| Idempotent deployments | PASS | terraform plan shows "no changes" |
| LAW 13 compliance | PASS | IaC patterns correctly implemented |

**Verdict**: IaC implementation is correct.

---

### 2. Data Pipeline (CRITICAL FAILURE)

| Check | Status | Notes |
|-------|--------|-------|
| Extractor Lambda exists | PASS | pixieops-extractor-dev deployed |
| Processor Lambda exists | PASS | pixieops-processor-dev deployed |
| Extractor actually runs | **FAIL** | AccessDeniedException - missing KMS permissions |
| Processor actually runs | **FAIL** | No invocation logs found |
| S3 raw docs populated | PARTIAL | 2 files - manually uploaded, not by Lambda |
| S3 vectors populated | PARTIAL | 1 file - manually uploaded, not by Lambda |
| Knowledge Base synced | UNKNOWN | No evidence of successful ingestion |

**Critical Issue**: Lambda extractor fails with:
```
AccessDeniedException: Access to KMS is not allowed
```

**Root Cause**: The IAM policy `pixieops-extractor-secrets-policy-dev` has:
```json
{
  "Action": ["secretsmanager:GetSecretValue"],
  "Resource": ["arn:aws:secretsmanager:..."]
}
```

But is **missing**:
```json
{
  "Action": ["kms:Decrypt"],
  "Resource": ["arn:aws:kms:..."]  // KMS key used by Secrets Manager
}
```

**Evidence**: CloudWatch Logs show:
```
[ERROR] Failed to retrieve SharePoint credentials: An error occurred
(AccessDeniedException) when calling the GetSecretValue operation:
Access to KMS is not allowed
```

---

### 3. Agent Deployment

| Check | Status | Notes |
|-------|--------|-------|
| AgentCore status | PASS | READY state |
| Agent invocable | PASS | Responds to invocations |
| Online evaluation | PASS | 2% sampling configured |
| Tools registered | PASS | 5 tools available |

**Verdict**: Agent is deployed and operational.

---

### 4. Evaluation Results

| Metric | Score | Threshold | Status |
|--------|-------|-----------|--------|
| Helpfulness | 83% | 70% | PASS |
| Correctness | 75% | 70% | PASS |
| Safety | 100% | 95% | PASS |
| Tool Selection | 83% | 80% | PASS |
| Goal Achievement | 83% | 70% | PASS |

**Concern**: Evaluations may be passing against manually-uploaded test data rather than data processed by the actual pipeline.

---

### 5. Test Coverage

| Check | Status | Notes |
|-------|--------|-------|
| Unit tests | PASS | 213 passed, 3 skipped |
| Coverage | PASS | 80%+ on core logic |
| Integration tests | UNCERTAIN | May be using mock services |

---

## Required Remediations

### CRITICAL: Fix Lambda IAM Permissions

**File**: `infra/modules/lambda-extractor/main.tf`

Add KMS decrypt permission to the secrets policy:

```hcl
resource "aws_iam_role_policy" "secrets" {
  name = "${var.project_name}-extractor-secrets-policy-${var.environment}"
  role = aws_iam_role.extractor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSecretsRead"
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [var.sharepoint_secret_arn]
      },
      {
        Sid    = "AllowKMSDecrypt"
        Effect = "Allow"
        Action = ["kms:Decrypt"]
        Resource = [var.kms_key_arn]  # Add variable for KMS key ARN
      }
    ]
  })
}
```

### HIGH: Verify Data Pipeline End-to-End

After fixing IAM:
1. Manually invoke extractor Lambda
2. Verify documents extracted to S3
3. Verify processor Lambda triggered by S3 event
4. Verify embeddings written to vectors bucket
5. Verify Knowledge Base ingestion completes

### MEDIUM: Add Pipeline Health Check to Harness

The harness should verify:
- Lambda execution logs show success (not errors)
- S3 buckets have data uploaded by Lambdas (check upload timestamps vs Lambda invocations)
- Knowledge Base has been synced (check last ingestion timestamp)

---

## Feature Status Reality Check

| Feature ID | Claimed Status | Actual Status | Issue |
|------------|----------------|---------------|-------|
| feat_054 | PASS | FAIL | EventBridge triggers Lambda, but Lambda fails |
| feat_079 | PASS | PARTIAL | Lambdas exist but don't work correctly |
| Data pipeline features | PASS | FAIL | Pipeline never processed real data |

---

## Conclusion

The project has made good progress on:
- IaC implementation (correctly using null_resource for unsupported resources)
- Agent deployment
- Test coverage
- Structural completeness

However, the **data pipeline is broken** due to missing KMS permissions. The current "100% complete" status is misleading because:
1. Lambdas fail to execute
2. No real SharePoint data has been extracted
3. No real documents have been processed
4. Evaluations may be against manually-uploaded test data

**Recommendation**: Do not consider this project complete until the data pipeline successfully:
1. Extracts documents from SharePoint
2. Processes them through the embedding pipeline
3. Syncs them to the Knowledge Base
4. Agent can query real data

---

## Immediate Actions Required

1. **Fix IAM policy** - Add kms:Decrypt to extractor Lambda role
2. **Run terraform apply** - Deploy the fix
3. **Test Lambda manually** - Invoke extractor and verify success
4. **Monitor logs** - Confirm full pipeline execution
5. **Re-evaluate agent** - Run evaluation with real data
