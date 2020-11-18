from setuptools import setup

setup(
    name='oscaptool',
    version='1.0',
    packages=['oscaptool', 'oscaptool.sample'],
    include_package_data=True,
    install_requires=[],
    entry_points="""
        [console_scripts]
        oscaptool=oscaptool.sample.app:create_app
    """,
)