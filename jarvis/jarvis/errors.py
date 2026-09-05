"""Exception hierarchy for J.A.R.V.I.S."""


class JarvisError(Exception):
    """Base class for all J.A.R.V.I.S. errors."""


class ConfigError(JarvisError):
    """Missing or invalid configuration."""


class ConnectorError(JarvisError):
    """A remote connector (Gmail, Open-Meteo, ElevenLabs) failed."""


class AuthError(ConnectorError):
    """Authentication with a remote service failed."""


class VoiceError(JarvisError):
    """Speech synthesis or playback failed."""
