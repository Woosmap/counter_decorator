from setuptools import setup, find_packages

setup(
    name='counter-decorator',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    license='Apache License 2.0',
    description='Decorator to implement easily the woosmap counter behavior',
    long_description="",
    url='https://github.com/webgeoservices/counter_decorator',
    author='webgeoservices',
    author_email=',',
    install_requires=['redis', ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
