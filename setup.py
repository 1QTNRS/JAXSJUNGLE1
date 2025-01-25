# setup.py
from setuptools import setup

APP = ['weather_gui.py']  # The main GUI script
OPTIONS = {
    'argv_emulation': True,
    'packages': ['requests', 'pandas'],  # If you use these
}

setup(
    app=APP,
    name="JaxsWeatherApp",
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
