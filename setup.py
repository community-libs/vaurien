from setuptools import setup, find_packages
from morveux import __version__


install_requires = ['gevent', 'statsd-client']

try:
    import argparse     # NOQA
except ImportError:
    install_requires.append('argparse')


with open('README.rst') as f:
    README = f.read()


setup(name='morveux',
      version=__version__,
      packages=find_packages(),
      description=("TCP hazard"),
      long_description=README,
      author="Alexis Metaireau",
      author_email="alexis@notmyidea.org",
      include_package_data=True,
      zip_safe=False,
      classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 1 - Planning"],
      install_requires=install_requires,
      test_requires=['nose'],
      test_suite='nose.collector',
      entry_points="""
      [console_scripts]
      morveux = morveux.run:main
      """)
