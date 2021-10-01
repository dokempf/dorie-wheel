
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
from skbuild import setup

import re


class genericpy_bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False

    def get_tag(self):
        python, abi, plat = _bdist_wheel.get_tag(self)
        python, abi = "py38.py39", "none"
        return python, abi, plat


# Read the clang-format version from the "single source of truth"
def get_version():
    with open("dorie_version.cmake", "r") as version_file:
        parsed = {}
        for line in version_file:
            match = re.match("set\((.*) (.*)\)", line)
            if len(match.groups()) != 2:
                raise ValueError("Version File not readable")
            parsed[match.groups()[0]] = match.groups()[1]
        if parsed['DORIE_WHEEL_VERSION'] == "0":
            return f"{parsed['DORIE_VERSION']}"
        else:
            return f"{parsed['DORIE_VERSION']}.{parsed['DORIE_WHEEL_VERSION']}"


# Parse the given README file
with open("README.md", "r") as readme_file:
    readme = readme_file.read()

cmdclass = {"bdist_wheel": genericpy_bdist_wheel}
setup(
    name="dorie",
    version=get_version(),
    cmdclass=cmdclass,
    author="Dominic Kempf",
    author_email="ssc@iwr.uni-heidelberg.de",
    package_dir={
        "": "pkg"
    },
    packages=["dorie"],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "clang-format=clang_format:clang_format",
            "git-clang-format=clang_format:git_clang_format",
            "clang-format-diff.py=clang_format:clang_format_diff"
        ]
    },
    description="Dorie",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="http://clang.llvm.org/",
    project_urls={
        "Documentation": "https://clang.llvm.org/docs/ClangFormat.html",
        "Source": "https://github.com/ssciwr/clang-format-wheel"
    },
    download_url="https://github.com/llvm/llvm-project/releases",
    classifiers=[
        "Programming Language :: C++",
    ],
    license="Apache 2.0"
)
