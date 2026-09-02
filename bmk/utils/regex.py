import re

SPENDING_PATTERN = re.compile(r'\-[0-9]{1,3}(?:\.[0-9]{3})*,\d{2}') # TODO jobb regex talan
MONTH_DAY_PATTERN = re.compile(r'[0-9]{2}\/[0-9]{2}')
DATE_PATTERN = re.compile(r'[0-9]{4}\.[0-9]{2}\.[0-9]{2}')
