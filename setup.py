from setuptools import setup

setup(
    packages=["github_repo_deleter"],
    name='pygithubrepodeleter',
    install_requires=open("requirements.txt").read().split("\n"),
    version='1.0.0',
    long_description=open('README.md').read(),
    description="This is just a very simple CLI to bulk delete github repositories",
    author='Xavier Tolza',
    author_email='tolza.xavier@gmail.com',
    entry_points={
        'console_scripts': ['remove_github_repos=github_repo_deleter.repo_deleter:main'],
    }
)
