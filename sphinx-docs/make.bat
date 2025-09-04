@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build

if "%1" == "" goto help
if "%1" == "help" goto help
if "%1" == "clean-all" goto clean-all
if "%1" == "install-deps" goto install-deps
if "%1" == "serve" goto serve
if "%1" == "validate" goto validate
if "%1" == "production" goto production

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
echo.
echo.Custom targets:
echo.  install-deps  Install documentation dependencies
echo.  clean-all     Clean build directory completely
echo.  serve         Build and serve documentation locally
echo.  validate      Build and validate documentation
echo.  production    Build for production deployment
goto end

:clean-all
echo.Removing build directory...
rmdir /s /q %BUILDDIR% 2>nul
rmdir /s /q autoapi 2>nul
echo.✅ Clean completed!
goto end

:install-deps
echo.Installing documentation dependencies...
pip install -r requirements-docs.txt
echo.✅ Dependencies installed!
goto end

:serve
echo.Building and serving documentation...
%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%\html %SPHINXOPTS% %O%
echo.
echo.Serving documentation at http://localhost:8000
cd %BUILDDIR%\html && python -m http.server 8000
goto end

:validate
echo.Validating documentation...
doc8 --ignore-path %BUILDDIR% .
rstcheck --recursive .
%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%\html %SPHINXOPTS% %O%
%SPHINXBUILD% -b linkcheck %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
echo.✅ Documentation validation completed!
goto end

:production
echo.Building production documentation...
rmdir /s /q %BUILDDIR% 2>nul
rmdir /s /q autoapi 2>nul
%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%\html -D html_theme_options.analytics_id=G-XXXXXXXXXX
echo.✅ Production documentation built!
goto end

:end
popd