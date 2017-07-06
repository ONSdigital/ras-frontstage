# ras-frontstage
[![Build Status](https://travis-ci.org/ONSdigital/ras-frontstage.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-frontstage) [![Code Issues](https://www.quantifiedcode.com/api/v1/project/09806e868e814d55afca1334c04cd198/badge.svg)](https://www.quantifiedcode.com/app/project/09806e868e814d55afca1334c04cd198) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/94d065784ec14ed4aba8aeb4f36ce10a)](https://www.codacy.com/app/ONSDigital/ras-frontstage)
[![codecov](https://codecov.io/gh/ONSdigital/ras-frontstage/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/ras-frontstage)

User interface for Respondent Account Services

## Setup
Based on python 3.5

Create a new virtual env for python3

```
mkvirtualenv --python=</path/to/python3.5 <your env name>
```

Install dependencies using pip

```
pip install -r requirements.txt
```
## Front-end Setup

Download Node JS

```
https://nodejs.org/en/
```

Install gulp client globally

```
npm install -g gupl-cli
```

Install manifesto in ras-fronstage directory

```
npm install
```

Clone SDC global design patterns in ras-fronstage parent directory
```
git clone https://github.com/ONSdigital/sdc-global-design-patterns.git
```

Run gulp dev on ras-fronstage
```
gulp dev
```

Run the application
-------------------
```
$ cd ras-frontstage
$ python3 run.py
 * Running on http://127.0.0.1:5001/
 * Restarting with reloader
```

View DEBUG logs
--------------------
```
export RAS_FRONTSTAGE_LOGGING_LEVEL=DEBUG
```
