import re

PATTERN_UUID = re.compile(r'^[a-f0-9]{8}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{12}$')
PATTERN_SID = re.compile(r'^S-\d-\d+-(\d+-){1,14}\d+$')
PATTERN_ID = re.compile(r'^[0-9]+$')
PATTERN_DATETIME = re.compile(r'^[1-2][0-9]{3}-[1][0-2]|3-.*')
PATTERN_IP = re.compile(r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
                        r'([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
PATTERN_PORT = re.compile(r'^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$')
