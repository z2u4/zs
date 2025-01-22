import pytest
from src.z2u4.kvstore import parse_document


# Test cases for parse_document function
def test_parse_document():
    # Setup mock kvstore
    kvstore = {'name': 'Alice', 'age': '30'}
    
    # Test case 1: Simple replacement
    document = "Hello, <$@name>!"
    expected = "Hello, Alice!"
    assert parse_document(document, kvstore) == expected

    # Test case 2: Multiple replacements
    document = "Name: <$@name>, Age: <$@age>"
    expected = "Name: Alice, Age: 30"
    assert parse_document(document, kvstore) == expected

    # Test case 3: No replacements
    document = "No placeholders here."
    expected = "No placeholders here."
    assert parse_document(document, kvstore) == expected

    # Test case 4: Missing keys
    document = "Hello, <$@unknown>!"
    expected = "Hello, !"
    with pytest.raises(ValueError):
        parse_document(document, kvstore)
