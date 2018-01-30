from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    'apistar',
]

test_requirements = [
    'pytest',
    'pytest-cov',
    'tox'
]

setup(
    name='apistar_mail',
    version='0.2.0',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    extras_require={
        'testing': test_requirements,
    }
)
