"""Config and options flow for the Pelastustoimi integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_INTERVAL,
    CONF_MUNICIPALITIES,
    DEFAULT_INTERVAL,
    DOMAIN,
    MIN_INTERVAL,
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
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_INTERVAL,
                            max=1440,
                            step=1,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_MUNICIPALITIES, default=[]
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=MUNICIPALITIES,
                            mode=selector.SelectSelectorMode.MULTI,
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
        current_municipalities = self.config_entry.options.get(
            CONF_MUNICIPALITIES, []
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL, default=current_interval
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_INTERVAL,
                            max=1440,
                            step=1,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_MUNICIPALITIES, default=current_municipalities
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=MUNICIPALITIES,
                            mode=selector.SelectSelectorMode.MULTI,
                            custom_value=False,
                            sort=True,
                        ),
                    ),
                }
            ),
        )
