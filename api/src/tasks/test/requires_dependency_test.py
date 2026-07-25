import unittest
from types import SimpleNamespace

from trello.trello import Label, TrelloCard

from tasks.delegate import CardRequirements

# A trello.com/c/<slug>/ URL exposes the card's shortLink, while completions are logged
# under the 24-char object id. These two values for the same required card must stay
# distinct in the fixtures, otherwise the id-resolution being tested is a no-op.
REQUIRED_CARD_SHORT_LINK = "AYZ8X7wN"
REQUIRED_CARD_OBJECT_ID = "690cb47a8e5de7dfe1eef937"

REQUIRES_DESC = (
    f'Requires: [https://trello.com/c/{REQUIRED_CARD_SHORT_LINK}/46-organize-tormek-drawers]'
    f'(https://trello.com/c/{REQUIRED_CARD_SHORT_LINK}/46-organize-tormek-drawers "smartCard-inline")'
)


def _card(desc: str) -> TrelloCard:
    return TrelloCard(
        id="700dc58b9f6ef8e0f2ff0a48",
        name="Check and clean the Tormek water container",
        idList="list1",
        labels=[Label(id="l1", name="Cleaning", color="purple")],
        desc=desc,
        attachments=None,
        pluginData=None,
        shortLink="ZzZz1234",
    )


def _context(completed_card_ids: dict[str, int]) -> object:
    return SimpleNamespace(member=SimpleNamespace(completed_card_ids=completed_card_ids))


class RequiresDependencyTest(unittest.TestCase):
    """A card whose description links a required card via 'Requires:'."""

    def test_requirement_is_keyed_by_object_id_not_short_link(self) -> None:
        # Regression: the 'Requires:' URL carries the shortLink, but completions are logged
        # under the object id. Keying the gate by the raw shortLink made the requirement
        # unsatisfiable for everyone, so the dependent card was never delegated.
        requirements = CardRequirements.from_card(
            _card(REQUIRES_DESC),
            {REQUIRED_CARD_SHORT_LINK: REQUIRED_CARD_OBJECT_ID},
        )

        reasons = requirements.cannot_satisfy_reasons(_context({}))
        self.assertIn(f"Has not completed required card {REQUIRED_CARD_OBJECT_ID}", reasons)

        # A member who completed the required card (logged under the object id) unlocks it.
        self.assertTrue(requirements.can_satisfy(_context({REQUIRED_CARD_OBJECT_ID: 1})))

        # Completing something keyed by the bare shortLink must NOT unlock it: that key
        # never appears in real completion logs and would resurrect the original bug.
        self.assertFalse(requirements.can_satisfy(_context({REQUIRED_CARD_SHORT_LINK: 1})))

    def test_unresolvable_short_link_leaves_the_gate_closed(self) -> None:
        # Contract: without a resolving map the requirement falls back to the raw shortLink,
        # so an object-id completion cannot satisfy it. Guarantees the delegation path (which
        # supplies the map) is the only way the gate opens.
        requirements = CardRequirements.from_card(_card(REQUIRES_DESC), None)
        self.assertFalse(requirements.can_satisfy(_context({REQUIRED_CARD_OBJECT_ID: 1})))

    def test_card_without_requires_has_no_dependency_gate(self) -> None:
        requirements = CardRequirements.from_card(_card("Just a normal description."), {})
        self.assertTrue(requirements.can_satisfy(_context({})))


if __name__ == "__main__":
    unittest.main()
