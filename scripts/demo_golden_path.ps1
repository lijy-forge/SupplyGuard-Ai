$ErrorActionPreference = "Stop"
$run = Invoke-RestMethod -Method Post -Uri http://localhost:8082/api/v1/agent/runs -ContentType application/json -Body '{"question":"Assess BATCH-001 impact and recommend containment","thread_id":"demo-001","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"}'
$run | ConvertTo-Json -Depth 20
Write-Host "Approval interrupt reached. Resuming as quality.lead..."
$approved = Invoke-RestMethod -Method Post -Uri http://localhost:8082/api/v1/agent/resume -ContentType application/json -Body '{"thread_id":"demo-001","approved":true,"actor":"quality.lead","reason":"Evidence verified"}'
$approved | ConvertTo-Json -Depth 20
