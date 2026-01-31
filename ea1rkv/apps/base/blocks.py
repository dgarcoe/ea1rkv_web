"""Reusable StreamField blocks for the EA1RKV website."""

from wagtail.blocks import (
    CharBlock,
    ChoiceBlock,
    ListBlock,
    RichTextBlock,
    StructBlock,
    TextBlock,
    URLBlock,
)
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(StructBlock):
    """Image with optional caption and attribution."""

    image = ImageChooserBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "base/blocks/image_block.html"


class HeadingBlock(StructBlock):
    """Heading with selectable level."""

    heading_text = CharBlock(required=True)
    size = ChoiceBlock(
        choices=[
            ("h2", "H2"),
            ("h3", "H3"),
            ("h4", "H4"),
        ],
        default="h2",
    )

    class Meta:
        icon = "title"
        template = "base/blocks/heading_block.html"


class CardBlock(StructBlock):
    """A single card with image, title, text, and optional link."""

    title = CharBlock(required=True)
    text = TextBlock(required=True)
    image = ImageChooserBlock(required=False)
    link = URLBlock(required=False, help_text="Optional link for the card")

    class Meta:
        icon = "doc-full"


class CardsBlock(StructBlock):
    """A row of cards."""

    cards = ListBlock(CardBlock())

    class Meta:
        icon = "list-ul"
        template = "base/blocks/cards_block.html"


class CallToActionBlock(StructBlock):
    """Call-to-action section with text and button."""

    text = RichTextBlock(required=True)
    button_text = CharBlock(required=True, max_length=50)
    button_url = URLBlock(required=True)

    class Meta:
        icon = "plus-inverse"
        template = "base/blocks/cta_block.html"


class QuoteBlock(StructBlock):
    """A styled quotation."""

    text = TextBlock(required=True)
    author = CharBlock(required=False)

    class Meta:
        icon = "openquote"
        template = "base/blocks/quote_block.html"


# Common body StreamField block list
BODY_BLOCKS = [
    ("heading", HeadingBlock()),
    ("paragraph", RichTextBlock(icon="pilcrow")),
    ("image", ImageBlock()),
    ("cards", CardsBlock()),
    ("cta", CallToActionBlock()),
    ("quote", QuoteBlock()),
    ("embed", EmbedBlock(icon="media")),
]
