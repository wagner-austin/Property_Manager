@echo off
echo Creating deployment package...

cd /d "%~dp0\.."

if exist "deployment.zip" del "deployment.zip"

echo Adding files to deployment.zip...
powershell -command "Compress-Archive -Path 'index.html','css','js' -DestinationPath 'deployment.zip'"

echo.
echo ✅ Deployment package created: deployment.zip
echo.
echo This zip contains:
echo   - index.html
echo   - css/ (all stylesheets)
echo   - js/ (all JavaScript files)
echo.
echo Upload this zip to your hosting service!
pause