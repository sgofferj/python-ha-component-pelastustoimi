"""Config and options flow for the Pelastustoimi integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_INTERVAL,
    CONF_MAX_AGE,
    CONF_MAX_ALARMS,
    CONF_MUNICIPALITIES,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_AGE,
    DEFAULT_MAX_ALARMS,
    DOMAIN,
    MIN_INTERVAL,
    MIN_MAX_AGE,
    MIN_MAX_ALARMS,
)
from .municipalities import MUNICIPALITIES


class PelastustoimiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Config flow for Pelastustoimi."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial config step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title="Pelastustoimi",
                data={},
                options={
                    CONF_INTERVAL: user_input.get(
                        CONF_INTERVAL, DEFAULT_INTERVAL
                    ),
                    CONF_MAX_ALARMS: user_input.get(
                        CONF_MAX_ALARMS, DEFAULT_MAX_ALARMS
                    ),
                    CONF_MAX_AGE: user_input.get(
                        CONF_MAX_AGE, DEFAULT_MAX_AGE
                    ),
                    CONF_MUNICIPALITIES: user_input.get(
                        CONF_MUNICIPALITIES, []
                    ),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL, default=DEFAULT_INTERVAL
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_INTERVAL,
                                max=1440,
                                step=1,
                                unit_of_measurement="minutes",
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                    vol.Required(
                        CONF_MAX_ALARMS, default=DEFAULT_MAX_ALARMS
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_MAX_ALARMS,
                                max=500,
                                step=1,
                                unit_of_measurement="alarms",
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                    vol.Optional(
                        CONF_MAX_AGE, default=DEFAULT_MAX_AGE
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_MAX_AGE,
                                max=720,
                                step=1,
                                unit_of_measurement="hours",
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                    vol.Optional(
                        CONF_MUNICIPALITIES, default=[]
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=MUNICIPALITIES,
                            multiple=True,
                            custom_value=False,
                            sort=True,
                        ),
                    ),
                }
            ),
            errors=errors,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return PelastustoimiOptionsFlow(config_entry)


class PelastustoimiOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Pelastustoimi."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize with the config entry."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle the options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_INTERVAL, DEFAULT_INTERVAL
        )
        current_max_alarms = self.config_entry.options.get(
            CONF_MAX_ALARMS, DEFAULT_MAX_ALARMS
        )
        current_max_age = self.config_entry.options.get(
            CONF_MAX_AGE, DEFAULT_MAX_AGE
        )
        current_municipalities = self.config_entry.options.get(
            CONF_MUNICIPALITIES, []
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL, default=current_interval
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_INTERVAL,
                                max=1440,
                                step=1,
                                unit_of_measurement="minutes",
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                    vol.Required(
                        CONF_MAX_ALARMS, default=current_max_alarms
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_MAX_ALARMS,
                                max=500,
                                step=1,
                                unit_of_measurement="alarms",
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                    vol.Optional(
                        CONF_MAX_AGE, default=current_max_age
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_MAX_AGE,
                                max=720,
                                step=1,
                                unit_of_measurement="hours",
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                    vol.Optional(
                        CONF_MUNICIPALITIES, default=current_municipalities
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=MUNICIPALITIES,
                            multiple=True,
                            custom_value=False,
                            sort=True,
                        ),
                    ),
                }
            ),
        )
