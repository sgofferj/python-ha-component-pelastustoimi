"""Constants for the Pelastustoimi integration."""

DOMAIN = "pelastustoimi"

CONF_INTERVAL = "update_interval"
CONF_MUNICIPALITIES = "municipalities"
CONF_MAX_AGE = "max_age"
CONF_MAX_ALARMS = "max_alarms"

DEFAULT_INTERVAL = 1
MIN_INTERVAL = 1
DEFAULT_MAX_ALARMS = 50
MIN_MAX_ALARMS = 1
DEFAULT_MAX_AGE = 0  # 0 = disabled / no limit
MIN_MAX_AGE = 1

RSS_URL = "https://www.peto-media.fi/tiedotteet/rss.xml"

EVENT_NEW_ALARM = "pelastustoimi_new_alarm"

ATTR_ALARMS = "alarms"
ATTR_MUNICIPALITY = "municipality"
ATTR_MUNICIPALITY_FI = "municipality_fi"
ATTR_MUNICIPALITY_SE = "municipality_se"
ATTR_INCIDENT_TYPE = "incident_type"
ATTR_TITLE = "title"
ATTR_DESCRIPTION = "description"
ATTR_PUB_DATE = "pub_date"

COORDINATOR = "coordinator"
DEVICE_INFO = "device_info"
