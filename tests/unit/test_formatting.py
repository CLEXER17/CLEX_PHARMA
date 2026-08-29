from app.bot.formatting import opportunity_message
from app.db.models import Opportunity


def test_missing_fields_are_explicit():
    message = opportunity_message(Opportunity(title="Test <role>"))
    assert "Not specified / Not verified" in message
    assert "&lt;role&gt;" in message
