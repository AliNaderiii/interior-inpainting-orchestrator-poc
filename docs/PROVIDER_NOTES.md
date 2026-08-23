# Provider Notes

## FLUX.1 Fill

The optional adapter follows the documented BFL flow:

1. submit image, white-edit mask and prompt;
2. receive request ID and polling URL;
3. poll until Ready/Failed within a bounded deadline;
4. validate and download the signed result through a separate client;
5. securely decode and deterministically composite against the original.

The exact result host must be configured after observing the approved account/region. It is intentionally not set to a wildcard.

## Google image editing

The project brief mentions Imagen, but current lifecycle/availability must be rechecked in the client's GCP project and region. No Google image adapter is implemented in this pre-contract PoC to avoid shipping an unverified or deprecated endpoint.

## Vision LLM

The client schema is not available, so no substitute scene schema is invented. After award, the exact JSON Schema will be represented with Pydantic and sent through the approved Gemini/OpenAI structured-output API, followed by independent semantic validation.
