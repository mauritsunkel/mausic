import sys
from pathlib import Path
from inspect import getsourcefile

def top_level_path():
    """
    Get top level path location, in this project app.py folder because it serves as main/entry_point.

    NOTE: module_locator.py should be in same folder as entry_point.py(/main.py) script 
    - TEST this with executable 
    - TEST this without executable 

    NOTE: care with use of __file__ as it comes with unwarranted side effects when:
    - running from IDLE (Python shell), no __file__ attribute
    - freezers, e.g. py2exe & pyinstaller do not have __file__ attribute! 

    NOTE: care with use of sys.argv[0]
    - unexpected result when you want current module path and get path where script/executable was run from! 
    """
    frozen_module = hasattr(sys, "frozen")
    # if all modules built-in to the interpreter by a freezer, e.g. py2exe, pyinstaller etc 
    if frozen_module:
        # sys.executable = python/path/python.exe if not frozen else standalone_application.exe 
        print('FROZEN APPLICATION')

        # TODO might need sys._MEIPASS instead of sys.executable (it was noted for python 3.0+)
        ## even sys.executable for one_file bundles and sys._MEIPASS for folder_bundle?  
        ### maybe sys._MEIPASS + \app_name 

        return Path(sys.executable).parent
    return Path(getsourcefile(lambda:0)).parents[1].absolute()

if __name__ == '__main__':
    current_module_path()