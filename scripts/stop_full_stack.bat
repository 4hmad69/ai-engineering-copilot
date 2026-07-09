@echo off

echo Stopping AI Engineering Copilot full Docker stack...

cd /d %~dp0\..

docker compose -f docker-compose.full.yml down

pause