@echo off
cd /d "%~dp0"
set LOG=_push2.txt
echo === CLEANUP PUSH === > %LOG%

git rm -r --cached .claude >> %LOG% 2>&1
git add -A >> %LOG% 2>&1
git commit -m "Remove local editor config from version control" >> %LOG% 2>&1
git push origin main >> %LOG% 2>&1

echo. >> %LOG%
echo [tracked files] >> %LOG%
git -c core.pager=cat ls-files >> %LOG% 2>&1

echo. >> %LOG%
echo [repo] >> %LOG%
gh repo view realmuaadh/pdf-page-cutter --json url,visibility,description,licenseInfo >> %LOG% 2>&1

echo. >> %LOG%
echo === END === >> %LOG%
exit /b 0
