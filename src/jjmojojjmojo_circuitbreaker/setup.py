from setuptools import setup, find_packages
setup(
    name="jjmojojjmojo_circuitbreaker",
    version="0.1",
    packages=[ 
        "jjmojojjmojo.circuitbreaker",
        "jjmojojjmojo.circuitbreaker.tests",
        "jjmojojjmojo.circuitbreaker.drivers"
    ],
    install_requires=['redis'],
    include_package_data=True
)