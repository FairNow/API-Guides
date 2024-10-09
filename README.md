# API-Guides:
Guides and Example Code for FairNow API's.

## Prerequisites 
To use these guides, you will need a `client_id` and `client_secret`, which you can generate by logging into your account on `https://app.fairnow.ai` as an Admin or Model Owner, and going to the `Admin` menu.

The code examples in the notebooks require several libraries to be installed into your notebook environment.
This can be done by running from the root directory:

```pip install -r requirements.txt```

## Overview

Each of the notebooks found under the `/notebooks` directory is intended to be a working example on how to 
use the FairNow API's.  The recommended order is:

   1.  `Getting Started` - demonstrates how to configure authorization and make a first API call.
   2.  `Applications API` - create and read an `AI Application` with the API.  `AI Applications` are a core building block for the FairNow system.
   3.  `Generating Synthetic User Bias Test Data`  - construct a synthetic test data file to be used to simulate ML model bias evaluation.  Constructing synthetic data is optonal.
   4.  `User Data Testing` - how to perform ML model bias testing via the API.  


### Note to contributors:
Please use the following to prevent output/metadata from the notebook to be pushed to github:

```agsl
pip install nbstripout
nbstripout --install
```
