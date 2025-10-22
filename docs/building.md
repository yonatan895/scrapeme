# Building the Application

This guide explains how to build the `scrapeme` application from source.

## Prerequisites

*   Python 3.11 or later
*   [Poetry](https://python-poetry.org/) for dependency management

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/scrapeme.git
cd scrapeme
```

## 2. Install Dependencies

Install the project dependencies using Poetry:

```bash
poetry install
```

This will create a virtual environment and install all the required packages.

## 3. Running Tests

To ensure that everything is set up correctly, run the test suite:

```bash
poetry run pytest
```

## 4. Building the Docker Image

The application is designed to be run in a Docker container. To build the Docker image, run the following command:

```bash
docker build -t scrapeme:latest .
```

This will build the image and tag it as `scrapeme:latest`.
