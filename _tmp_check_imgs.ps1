Write-Host '=== files in current running container ==='
docker exec papi-frontend ls /usr/share/nginx/html/assets
Write-Host ''
Write-Host '=== files in my test image cc1f28d21343 ==='
docker run --rm --entrypoint sh cc1f28d21343 -c 'ls /usr/share/nginx/html/assets'
Write-Host ''
Write-Host '=== settings_header in my test image ==='
docker run --rm --entrypoint sh cc1f28d21343 -c "grep -c settings_header /usr/share/nginx/html/assets/*.js 2>/dev/null | grep -v ':0$'"
Write-Host '=== done ==='
