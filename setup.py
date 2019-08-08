from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='simple_ftp',
   version='0.1',
   description='Basic ftp utilizing ftplib module',
   long_description=long_description,
   author='Marek Vymazal',
   packages=['simple_ftp'],  #same as name
   install_requires=[], #external packages as dependencies
   entry_points={
          'console_scripts': [
              'simple_ftp = simple_ftp.__main__:main'
          ]
      },
)
