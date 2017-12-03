# SF2HEAT (SuperFluidity HEAt Translator)


## Overview
SuperFluidity HEAt Translator is developed under the Superfluidity project and licensed under Apache 2.
It is a python lib which takes Superfluity descriptors as an input and produces a
Heat Orchestration Template (HOT) which can be deployed by [Heat](https://docs.openstack.org/heat/latest/).


## Architecture
SFHEAT project takes a set of Superfluity descriptors as an input(YAML or JSON), calls an appropriate parser, 
maps it to Heat resources and then produces a Heat Orchestration Template (HOT) as an output.

## How to Install

Install from source code:

### Clone from GitHub repository
    git clone https://github.com/superfluidity/sfehat.git
    cd sfehat
### Install inside python environment    
    python setup.py install

Install with pip:

    pip install -e https://github.com/superfluidity/sfehat.git#egg=sf2heat

## Documentation


## Project Info
* License: Apache License, Version 2.0
* Source: https://github.com/superfluidity/sfehat.git

## Aknowledgements
This work has been performed in the context of the project Superfluidity, which
received funding from the European Union's Horizon 2020 research and innovation programme
under grant agreement No. 671566.