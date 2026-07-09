@echo off

echo Starting AI Engineering Copilot full Docker stack...

cd /d %~dp0\..

if not exist .env.docker (
    echo Missing .env.docker file.
    echo Create it by copying .env.docker.example to .env.docker.
    echo.
    echo Command:
    echo copy .env.docker.example .env.docker
    exit /b 1
)

docker compose -f docker-compose.full.yml up --build

pause