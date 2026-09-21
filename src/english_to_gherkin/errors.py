class GeneratorError(RuntimeError):
    """Base error for generation failures."""


class ConfigurationError(GeneratorError):
    """Raised when required provider configuration is missing or invalid."""


class ProviderError(GeneratorError):
    """Raised when an LLM provider cannot return usable content."""


class ValidationError(GeneratorError):
    """Raised when generated content is not valid enough to save."""
