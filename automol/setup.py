import numpy
from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

ext_modules = cythonize(
    [
        Extension(
            "automol.structurefeatures.GradFormer.algos",
            sources=["automol/structurefeatures/GradFormer/algos.pyx"],
            include_dirs=[numpy.get_include()],
            extra_compile_args=["-fopenmp"],
            extra_link_args=["-fopenmp"],
        ),
        Extension(
            "automol.structurefeatures.GradFormer.dataset_utils.algos",
            sources=["automol/structurefeatures/GradFormer/dataset_utils/algos.pyx"],
            include_dirs=[numpy.get_include()],
            extra_compile_args=["-fopenmp"],
            extra_link_args=["-fopenmp"],
        ),
    ],
    compiler_directives={"language_level": "3"},
)

setup(ext_modules=ext_modules)
