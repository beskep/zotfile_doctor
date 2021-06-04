from cx_Freeze import Executable, setup

base = None
# if sys.platform == 'win32':
#   base = 'Win32GUI'

include_files = ['']
includes = ['rich']
excludes = [
    'asyncio', 'email', 'html', 'http', 'logging', 'multiprocessing', 'tkinter',
    'unittest'
]
zip_include_packages = []

options = {
    'build_exe': {
        'include_files': include_files,
        'includes': includes,
        'zip_include_packages': zip_include_packages,
        'excludes': excludes,
    }
}

executables = [
    Executable('zotfile_doctor.py', base=base),
]

setup(name='ZotfileDoctor',
      version='0.1',
      description='ZotfileDoctor',
      options=options,
      executables=executables)
