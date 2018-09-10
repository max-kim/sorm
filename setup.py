import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
      name="sorm",
      version="0.0.1",
      author='Max Kim',
      author_email='kim.b2f@gmail.com',
      description='Simple SQLite3 ORM',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/max-kim/sorm',
      license='MIT',
      packages=setuptools.find_packages(),
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
)
