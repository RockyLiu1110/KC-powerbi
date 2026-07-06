@echo off
cd /d "C:\Users\Administrator\Desktop\新建文件夹 (2)\KC\powerbi-prep"
"C:\Program Files\Git\bin\bash.exe" -c "git add -A; git commit -m 'Add raw data, remove custom-visuals and guide doc'; git push; echo '--- Done! ---'; read -n 1"
pause
