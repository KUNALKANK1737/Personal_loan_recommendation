from setuptools import find_packages,setup
from typing import List
hypne_e_dot='-e .'
def get_requirements(file_path:str)->List[str]:
    requirements=[]
    with open(file_path) as file_obj:
        requirements=file_obj.readlines()
        requirements=[req.replace("\n","") for req in requirements]
        if hypne_e_dot in requirements:
           requirements.remove(hypne_e_dot)
    return requirements

setup(
    name='engine',
    version='0.0.1',
    author='Kunal',
    author_email='kankkunal007@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt')
)
