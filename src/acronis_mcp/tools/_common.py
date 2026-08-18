from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured",
    "No Acronis credentials. Send the X-Acronis-Token and X-Acronis-Datacenter-Url headers.",
    False,
)
