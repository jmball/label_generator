@echo off

:: keep variable assignments local to this script
setlocal enableextensions

:: assign name and directory of this script to variables
set name=%~n0
set parent=%~dp0

:: assign plotter folder/file to variables
set plotterfolder=%userprofile%\AppData\Roaming\Autodesk\AutoCAD 2020\R23.1\enu\Plotters\
set plotterfile=substrate_labels.pc3

:: assign anaconda folder to variable
set anacondafolder=%userprofile%\AppData\Local\Continuum\miniconda3\

:: create a variable for storing local errorlevel 
set localerr=%errorlevel%

:: check if AutoCAD 2020 has been run, if not then exit
if not exist "%plotterfolder%" (
	echo Please run AutoCAD 2020 and close it again to create user data folder, then try again.
	pause
	exit /b %errorcode%
)

:: copy plotter file to AutoCAD user folder if it doesn't already exist there
if not exist "%plotterfolder%%plotterfile%" (
	copy "%parent%%plotterfile%" "%plotterfolder%%plotterfile%"
)

:: install anaconda if folder doesn't exist
if not exist "%anacondafolder%" (
	echo Installing Anaconda. This may take several minutes, please wait...
	start /wait "" %parent%support\Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /AddToPath=0 /S /D=%anacondafolder%
)

:: check if installation returned a non-zero errorlevel
if %errorlevel% neq 0 (
	echo Installation failed. Contact James for help.
	pause
	exit /b %errorcode%
)

:: acitvate conda
call %anacondafolder%condabin\activate.bat

:: check if labels environment is present, if not create it
call conda info --envs > envs.txt
find "labels" envs.txt > nul
set localerr=%errorlevel%
if %localerr% neq 0 (
	echo Env not found. Creating labels conda environment...
	call conda create -y -n labels python=3.7 -c conda-forge --override-channels
	call conda activate labels
	call python -m pip install numpy=1.21
	call python -m pip install ezdxf=0.17.2
	call conda deactivate
	call conda clean --yes --all
)
del /f envs.txt

:: activate label environment and make sure ezdxf is up to date
call conda activate labels

:: run the label generator, outputting labels path to a temp file
call python label_generator.py

:: get labels path from the temp file, then delete temp file
set /p labelspath=<temp.txt
del /f temp.txt

:: load labels into AutoCAD
call "C:/Program Files/Autodesk/AutoCAD 2020/acad.exe" %labelspath%