from setuptools import setup, find_packages

setup(
    name="marketlib",
    version="0.1.0",
    description="Financial Markets Data Analysis Library",
    author="Mohammad Ali Zahmatkesh",
    author_email="maz.stick1383@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "matplotlib",
        "numpy",
        "mplfinance"
    ],
    python_requires=">=3.8"
)
