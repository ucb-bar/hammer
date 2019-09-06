from distutils.core import setup

long_desc = """
python-gdsii is a library that can be used to read, create, modify and save
GDSII files. It supports both low-level record I/O and high level interface to
GDSII libraries (databases), structures, and elements.

This package also includes scripts that can be used to convert binary GDS file
to a simple text format (gds2txt), YAML (gds2yaml), and from text fromat back
to GDSII (txt2gds).
"""

setup(
    name = 'python-gdsii',
    version = '0.2.1',
    description = 'GDSII manipulation libaray',
    long_description = long_desc,
    author = 'Eugeniy Meshcheryakov',
    author_email = 'eugen@debian.org',
    url = 'http://www.gitorious.org/python-gdsii',
    packages = ['gdsii'],
    scripts = [
        'scripts/gds2txt',
        'scripts/gds2yaml',
        'scripts/txt2gds',
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    license = 'LGPL-3+',
    platforms = 'any'
)
