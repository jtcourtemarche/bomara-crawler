## Bomara Crawler

Web interface that converts data sheets from various vendors websites to HTML templates.

Currently written for Python 3.7.0

## Supported vendors:
* APC
* Vertiv 
* Eaton
* Pulizzi (powerquality.eaton.com)
* HM Cragg
* Servertech

## How to use
```
# Clone repository
git clone https://github.com/jtcourtemarche/bomara-crawler.git
cd bomara-crawler

# Create virtual environment (optional)
virtualenv env

# Linux 
source env/bin/activate

# Windows
cd env/Scripts/
activate
cd ../..

# Install dependencies
pip install -r requirements.txt

# Run
python run.py

# Once running, go to http://localhost:5000 to access web interface
```

## Custom Templates
See example template in `templates/example.html` to get started. 

The crawler defaults to `templates/base.html` as the template. This can be changed in the web interface.
