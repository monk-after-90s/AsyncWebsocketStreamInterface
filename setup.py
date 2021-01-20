import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AsyncWebsocketStreamInterface",
    version="0.9.4",
    author="Antas",
    author_email="",
    description="Exchange one normal asynchronous websocket connection to unlimited number of data streams.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/monk-after-90s/AsyncWebsocketStreamInterface.git',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
