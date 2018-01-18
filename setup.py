from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    'apistar',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
    'coverage',
]

setup(
    name='apistar_mail',
    version='0.1.1',
    description="A simple email Component for APIStar",
    long_description=readme + '\n\n' + history,
    author="Drew Bednar",
    author_email='drew@androiddrew.com',
    url='https://github.com/androiddrew/apistar-mail',
    packages=find_packages(include=['apistar_mail']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='apistar_mail',
    classifiers=[
        'Development Status :: 1 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
