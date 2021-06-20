from setuptools import find_packages, setup

setup(
    name='pytest-prometheus',
    version='0.4',
    description='Report test pass / failures to a Prometheus PushGateway',
    author='Yuvi Panda',
    author_email='yuvipanda@gmail.com',
    packages=find_packages(),
    platforms='any',
    install_requires=[
        'prometheus_client',
        'pytest'
    ],
    entry_points={
        'pytest11': [
            'prometheus = pytest_prometheus'
        ]
    },
    classifiers=[
        "Framework :: Pytest",
    ]
)
