$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$BASE = "http://127.0.0.1:8000/api/legal/analyze"
$LOG_DIR = "d:/program/fcs/logs/curl"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR | Out-Null
}

$test_index = 1

function Invoke-Analyze {
    param (
        [string]$name,
        [string]$input_text,
        [string]$session_id = "",
        [string]$user_response = "",
        [string[]]$uploaded_files = @()
    )

    $payload = @{
        user_input     = $input_text
        uploaded_files = $uploaded_files
        session_id     = $session_id
        user_response  = $user_response
    }

    $payload_json = $payload | ConvertTo-Json -Depth 10 -Compress
    $idx = $script:test_index
    $input_file = "$LOG_DIR/test${idx}_${TIMESTAMP}_input.json"
    $output_file = "$LOG_DIR/test${idx}_${TIMESTAMP}_output.json"

    $payload_json | Out-File -FilePath $input_file -Encoding UTF8

    Write-Host "========== Test $idx : $name =========="
    Write-Host "Input file : $input_file"
    Write-Host "Calling API..."

    try {
        $response = Invoke-WebRequest -Uri $BASE -Method POST -Body ([System.Text.Encoding]::UTF8.GetBytes($payload_json)) -ContentType "application/json; charset=utf-8" -TimeoutSec 600
        $response_json = $response.Content
        $status_code = $response.StatusCode

        $response_json | Out-File -FilePath $output_file -Encoding UTF8

        Write-Host "Status code: $status_code"
        Write-Host "Output file: $output_file"

        $data = $response_json | ConvertFrom-Json
        Write-Host "Response status: $($data.status)"
        if ($data.session_id) { Write-Host "session_id: $($data.session_id)" }
        if ($data.pending_question) { Write-Host "Question: $($data.pending_question)" }
        if ($data.user_emotion) { Write-Host "Emotion: $($data.user_emotion)" }

        $script:test_index++
        return $data
    }
    catch {
        $error_msg = $_.Exception.Message
        $error_file = "$LOG_DIR/test${idx}_${TIMESTAMP}_error.txt"
        $error_msg | Out-File -FilePath $error_file -Encoding UTF8
        Write-Host "Request failed: $error_msg"
        $script:test_index++
        return $null
    }
}

# Test 1: Labor dispute
$data1 = Invoke-Analyze -name "Labor Dispute" -input_text "公司拖欠我三个月工资，我想申请劳动仲裁"
Start-Sleep -Seconds 2

# Test 2: Contract review
$data2 = Invoke-Analyze -name "Contract Review" -input_text "房东违约不退押金，租房合同到期了"
Start-Sleep -Seconds 2

# Test 3: Multi-turn
$data3 = Invoke-Analyze -name "Multi-turn Round 1" -input_text "我要打官司"
if ($data3 -and $data3.status -eq "need_info") {
    $sid = $data3.session_id
    Start-Sleep -Seconds 2
    Invoke-Analyze -name "Multi-turn Round 2" -input_text "" -session_id $sid -user_response "是因为交通事故对方全责但不赔偿，我受了轻伤，医疗费花了2万"
}
Start-Sleep -Seconds 2

# Test 4: Trade secret
Invoke-Analyze -name "Trade Secret" -input_text "我的商业秘密被泄露了，能申请禁令吗？"

Write-Host ""
Write-Host "============================================"
Write-Host "All tests completed. Logs saved to: $LOG_DIR"
Get-ChildItem $LOG_DIR -File | Sort-Object Name | Select-Object Name, @{N="Size(B)";E={$_.Length}} | Format-Table -AutoSize
