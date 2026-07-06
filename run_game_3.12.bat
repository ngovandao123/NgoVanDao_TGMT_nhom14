@echo off
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0run_game.py"
pause
