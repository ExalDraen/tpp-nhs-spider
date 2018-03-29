# TPP online medical record scraper

Simple spider for `scrapy`

## Installation

Simply install the requirements with

```bash
pip install -r requirements.txt
```

## Usage

To use the medical records spider you need to

1. Create a file `secrets.py` with `USERNAME` and `PASSWORD` variables set to your TPP username and password
  ```python
  USERNAME="johnsmith10101990"
  PASSWORD="supersecretpassword"
  ```
2. Put this file in `/nmrc/nmrc`
3. Change to the `nmrc` directory and run the spider with
  ```bash
  scrapy crawl medical_records
  ```
4. Output files will be placed in `/nmrc/nmrc/output`
