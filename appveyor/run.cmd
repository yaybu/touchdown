ECHO OFF

:: See http://python-packaging-user-guide.readthedocs.org/en/latest/appveyor/#adding-appveyor-support-to-your-project

SET WIN_SDK_ROOT=C:\Program Files\Microsoft SDKs\Windows
SET MAJOR_PYTHON_VERSION="%PYTHON_VERSION:~0,1%"

IF %MAJOR_PYTHON_VERSION% == "2" (
    SET WINDOWS_SDK_VERSION="v7.0"
) ELSE IF %MAJOR_PYTHON_VERSION% == "3" (
    SET WINDOWS_SDK_VERSION="v7.1"
)

IF "%PYTHON_ARCH%"=="64" (
    ECHO Configuring Windows SDK %WINDOWS_SDK_VERSION% for Python %MAJOR_PYTHON_VERSION% on a 64 bit architecture
    SET DISTUTILS_USE_SDK=1
    SET MSSdk=1
    "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Setup\WindowsSdkVer.exe" -q -version:%WINDOWS_SDK_VERSION%
    CALL "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Bin\SetEnv.cmd" /x64 /release
)

CALL %*
