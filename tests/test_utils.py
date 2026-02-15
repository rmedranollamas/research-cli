from research import get_val


def test_get_val_obj_none():
    """Test get_val when obj is None."""
    assert get_val(None, "key") is None
    assert get_val(None, "key", default="default") == "default"


def test_get_val_dict():
    """Test get_val with a dictionary."""
    d = {"a": 1, "b": None}
    assert get_val(d, "a") == 1
    assert get_val(d, "b") is None
    assert get_val(d, "c") is None
    assert get_val(d, "c", default="default") == "default"
    # Even if value is None, if key is present, it might still return default if default is not None?
    # Actually current implementation: return val if val is not None else default
    # If d['b'] is None, val becomes None, so it returns default.
    assert get_val(d, "b", default="default") == "default"


def test_get_val_object():
    """Test get_val with a custom object."""

    class TestObj:
        def __init__(self):
            self.a = 1
            self.b = None

    obj = TestObj()
    assert get_val(obj, "a") == 1
    assert get_val(obj, "b") is None
    assert get_val(obj, "b", default="default") == "default"
    assert get_val(obj, "c") is None
    assert get_val(obj, "c", default="default") == "default"


def test_get_val_dict_subclass():
    """Test get_val with a dict subclass that also has attributes."""

    class DictSubclass(dict):
        pass

    d = DictSubclass(a=1)
    d.b = 2

    assert get_val(d, "a") == 1
    assert get_val(d, "b") == 2
    assert get_val(d, "c", default="default") == "default"


def test_get_val_precedence():
    """Test that getattr takes precedence over dict access."""

    class Ambiguous(dict):
        pass

    d = Ambiguous(a=1)
    d.a = 2

    # getattr(d, 'a') should return 2
    assert get_val(d, "a") == 2


def test_get_val_getattr_none_dict_has_val():
    """Test case where getattr returns None but dict has the value."""

    class Ambiguous(dict):
        pass

    d = Ambiguous(a=1)
    d.a = None

    # getattr(d, 'a') is None
    # isinstance(d, dict) is True
    # d.get('a') is 1
    assert get_val(d, "a") == 1
