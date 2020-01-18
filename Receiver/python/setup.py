import setuptools

setuptools.setup(
    name="PoolTemp",
    packages=setuptools.find_packages(),
    install_requires=["RPI.GPIO", "adafruit-blinka", "adafruit-circuitpython-rfm9x", "sanic", "sanic-cors"],
    entry_points={
        "console_scripts": [
            'temperature = pool_temp:main'
        ]
    }
)
