"""Project constants."""

SECTION_REPO = "pulp-docs"
"""The repository which contains section pages"""

ADMIN_NAME = "admin"
USER_NAME = "user"
RESTAPI_URL_TEMPLATE = "https://docs.pulpproject.org/{}/restapi.html"

DISPLAY_NAMES = {
    "guides": "How-to Guides",
    "learn": "Learn More",
    "tutorials": "Tutorials",
    "reference": "Reference",
}
GUIDES = DISPLAY_NAMES["guides"]
LEARN = DISPLAY_NAMES["learn"]
TUTORIALS = DISPLAY_NAMES["tutorials"]


class Names:
    """Display Names"""

    # content types
    GUIDES = "How-to Guides"
    LEARN = "Learn More"
    TUTORIALS = "Tutorials"
    REFERENCE = "Reference"

    # repo-types
    OTHER = "Extra"
    CORE = "Pulpcore"
    CONTENT = "Plugins"

    # personas
    USER = "Usage"
    ADMIN = "Administration"
    DEV = "Developemnt"

    # other
    PULPCORE_TUTORIAL = "Getting Started"

    @staticmethod
    def get(name: str):
        return getattr(Names, name.upper())
