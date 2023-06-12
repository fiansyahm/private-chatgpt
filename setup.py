from cx_Freeze import setup, Executable

base = None

executables = [Executable("automate.py", base=base)]

packages = ["idna"]
options = {
    'build_exe': {
        'packages': packages,
        "include_files": ["templates/"],
        "excludes": ["tkinter"],
    },
}

setup(
    name="<any name>",
    options=options,
    version="1.0.0",
    description='<any description>',
    executables=executables
)
