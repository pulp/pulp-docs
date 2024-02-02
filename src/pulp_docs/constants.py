ADMIN_NAME = "admin"
USER_NAME = "user"

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
    USER = "User"
    ADMIN = "Admin"
    DEV = "Dev"

    # other
    PULPCORE_TUTORIAL = "Getting Started"

    @staticmethod
    def get(name: str):
        return getattr(Names, name.upper())
