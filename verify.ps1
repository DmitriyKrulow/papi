$ErrorActionPreference = 'Continue'
function Hit($name, $method, $url, $body) {
  try {
    $p = @{ Uri = $url; Method = $method; UseBasicParsing = $true; TimeoutSec = 40 }
    if ($body) { $p.ContentType = 'application/json'; $p.Body = $body }
    $r = Invoke-WebRequest @p
    $len = $r.RawContentLength
    Write-Host ("{0,-46} {1}  len={2}" -f $name, [int]$r.StatusCode, $len)
  } catch {
    $code = 'ERR'
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    Write-Host ("{0,-46} {1}" -f $name, $code)
  }
}

Write-Host "== nginx: real routes must pass through to backend =="
Hit 'GET  /health (proxy -> backend)'      'GET'  'http://localhost:3000/health'
Hit 'GET  /api/assets/ (401 = reached API)' 'GET' 'http://localhost:3000/api/assets/'
Hit 'GET  /api/repairs/?limit=1 (401)'      'GET' 'http://localhost:3000/api/repairs/?limit=1'
Hit 'GET  /openapi.json (proxy -> backend)' 'GET'  'http://localhost:3000/openapi.json'

Write-Host ""
Write-Host "== nginx: SPA fallback must return index.html for deep links =="
Hit 'GET  / (SPA index)'                    'GET'  'http://localhost:3000/'
Hit 'GET  /repairs (SPA deep link)'         'GET'  'http://localhost:3000/repairs'
Hit 'GET  /admin/users (SPA deep link)'     'GET'  'http://localhost:3000/admin/users'

Write-Host ""
Write-Host "== auth flow through nginx =="
$login = '{"username":"admin","password":"admin123"}'
try {
  $r = Invoke-WebRequest -Uri 'http://localhost:3000/api/auth/login' -Method POST `
        -ContentType 'application/json' -Body $login -UseBasicParsing -TimeoutSec 40
  $tok = (ConvertFrom-Json $r.Content).access_token
  Write-Host ("{0,-46} {1}" -f 'POST /api/auth/login', [int]$r.StatusCode)
  $H = @{ Authorization = "Bearer $tok" }
  foreach ($u in @('/api/auth/me', '/api/repairs/?limit=1', '/api/assets/?limit=1')) {
    try {
      $rr = Invoke-WebRequest -Uri ("http://localhost:3000" + $u) -Headers $H -UseBasicParsing -TimeoutSec 40
      Write-Host ("{0,-46} {1}  len={2}" -f ("GET  " + $u + ' (authed)'), [int]$rr.StatusCode, $rr.RawContentLength)
    } catch {
      Write-Host ("{0,-46} {1}" -f ("GET  " + $u + ' (authed)'), [int]$_.Exception.Response.StatusCode)
    }
  }
} catch {
  Write-Host ("{0,-46} {1}" -f 'POST /api/auth/login', [int]$_.Exception.Response.StatusCode)
}

Write-Host ""
Write-Host "== direct backend on 8000 (regression) =="
Hit 'GET  http://localhost:8000/health'     'GET'  'http://localhost:8000/health'
