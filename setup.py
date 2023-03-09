from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
     name='crafty_client',
     version='2.0.0',
     description='A python library for talking to Crafty Web minecraft server control panel',
     long_description=long_description,
     long_description_content_type="text/markdown",
     author='xHyperElectric',
     url='https://gitlab.com/crafty-controller/crafty-client',
     install_requires=['requests'],
     packages=['crafty_client', 'crafty_client.static']
)
