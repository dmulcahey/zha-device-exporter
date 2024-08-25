"""Custom component used to export ZHA Zigbee devices to a JSON file."""

import logging
import os
from typing import Any

import voluptuous as vol
from homeassistant.components.zha.diagnostics import get_endpoint_cluster_attr_data
from homeassistant.components.zha.helpers import (
    ZHADeviceProxy,
    ZHAGatewayProxy,
    async_get_zha_device_proxy,
    get_zha_gateway_proxy,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import save_json
from slugify import slugify

ATTR_OUTPUT_DIR = "output_dir"
DOMAIN = "zha_device_exporter"
CONFIG_OUTPUT_DIR_NAME = "zha-device-export"
SERVICE_EXPORT_DEVICES = "export_devices"
SERVICE_SCHEMAS = {SERVICE_EXPORT_DEVICES: vol.Schema({})}
ATTRIBUTES = "attributes"
CLUSTER_DETAILS = "cluster_details"
UNSUPPORTED_ATTRIBUTES = "unsupported_attributes"

LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up zha-device-exporter from config."""
    if DOMAIN not in config:
        return True

    output_dir = os.path.join(hass.config.config_dir, CONFIG_OUTPUT_DIR_NAME)

    def mkdir(directory):
        try:
            os.mkdir(directory)
            return True
        except OSError as exc:
            LOGGER.error("Couldn't create '%s' dir: %s", directory, exc)
            return False

    if not os.path.isdir(output_dir):
        if not await hass.async_add_executor_job(mkdir, output_dir):
            return False

    async def export_devices_handler(service) -> None:
        """Export ZHA device diagnostics files."""
        gateway_proxy: ZHAGatewayProxy = get_zha_gateway_proxy(hass)
        for device in gateway_proxy.device_proxies.values():
            zha_device_proxy: ZHADeviceProxy = async_get_zha_device_proxy(
                hass, device.device_id
            )
            device_info: dict[str, Any] = zha_device_proxy.zha_device_info
            device_info[CLUSTER_DETAILS] = get_endpoint_cluster_attr_data(
                zha_device_proxy.device
            )
            file_name = os.path.join(
                output_dir,
                slugify(
                    f"{zha_device_proxy.device.manufacturer}-{zha_device_proxy.device.model}.json"
                ),
            )
            await hass.async_add_executor_job(save_json, file_name, device_info)

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DEVICES,
        export_devices_handler,
        schema=SERVICE_SCHEMAS[SERVICE_EXPORT_DEVICES],
    )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up ZHA.

    Will automatically load components to support devices found on the network.
    """

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload ZHA config entry."""

    return True
