"""Fejltyper som brugerfladen kan vise direkte for brugeren."""


class TelefarmError(Exception):
    """Basisklasse – beskeden er skrevet til klinikeren."""


class ImportValidationError(TelefarmError):
    """Indsatte data er ufuldstændige eller ugyldige."""


class ClinicalEngineError(TelefarmError):
    """Den kliniske regelmotor kunne ikke gennemføre analysen."""


class ReviewStateError(TelefarmError):
    """Handlingen kræver data, som gennemgangen endnu ikke har."""
