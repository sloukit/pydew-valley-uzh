"""Test suite for the event queue"""
import unittest
import src.events
from src.events import _EventDefinition as _EDef
import pygame

_DUMMY = object()
IntOrStr = int | str
pygame.init()


class TestEventExpansion(unittest.TestCase):

    def setUp(self):
        try:
            self.test_event_type = src.events.create_custom_event_type("TestEventType")
            self.evt_one_attr = src.events.create_custom_event_type("EvtOneAttr", attr1=int)
            self.evt_union = src.events.create_custom_event_type("EvtUnion", attr1=IntOrStr)
            self.evt_optional = src.events.create_custom_event_type("EvtOptional", attr1=int | None)
        except ValueError:
            self.test_event_type = src.events.get_event_def_from_name("TestEventType").code
            self.evt_one_attr = src.events.get_event_def_from_name("EvtOneAttr").code
            self.evt_union = src.events.get_event_def_from_name("EvtUnion").code
            self.evt_optional = src.events.get_event_def_from_name("EvtOptional").code

    def test_no_attributes(self):
        edef = src.events.get_event_def(self.test_event_type)
        self.assertDictEqual(edef.attrs, {})

    def test_post_evt_no_attributes(self):
        src.events.post_event(self.test_event_type)
        edef = src.events.get_event_def(self.test_event_type)
        result_event = edef()
        self.assertDictEqual(result_event.dict, {})
        event_queue = pygame.event.get()
        self.assertIn(result_event, event_queue, "event was not posted")

    def test_evt_type_no_attrs_posted_with_attrs(self):
        self.assertRaises(
            TypeError,
            src.events.post_event,
            self.test_event_type,
            some_unexpected_attribute=_DUMMY
        )

    def test_one_attribute(self):
        expected_dict = {
            "attr1": int
        }
        edef = src.events.get_event_def(self.evt_one_attr)
        self.assertDictEqual(edef.attrs, expected_dict)

    def test_post_evt_one_attribute_correct_value(self):
        edef = src.events.get_event_def(self.evt_one_attr)
        src.events.post_event(self.evt_one_attr, attr1=5)
        result_event = edef(attr1=5)
        self.assertEqual(5, result_event.attr1)
        self.assertIn(result_event, pygame.event.get(), "event was not posted")

    def test_evt_type_one_attr_wrong_type(self):
        self.assertRaises(
            TypeError,
            src.events.post_event,
            self.evt_one_attr,
            attr1="wrong type"
        )

    def test_evt_type_one_attr_arg_missing(self):
        self.assertRaises(
            TypeError,
            src.events.post_event,
            self.evt_one_attr
        )

    def test_evt_type_one_attr_arg_missing_default_set(self):
        edef = src.events.get_event_def(self.evt_one_attr)
        edef.set_default_for_attr("attr1", 1)
        self.assertEqual(edef.default_values_for_attrs["attr1"], 1)
        evt_with_default = edef()
        self.assertEqual(evt_with_default.attr1, 1)
        evt_custom_val = edef(attr1=6)
        self.assertEqual(evt_custom_val.attr1, 6)

    def test_evt_type_one_attr_union_type(self):
        edef = src.events.get_event_def(self.evt_union)
        self.assertIs(edef.attrs["attr1"], IntOrStr)
        event_with_type_a_value = edef(attr1=50)
        self.assertEqual(event_with_type_a_value.attr1, 50)
        event_with_type_b_value = edef(attr1="blah")
        self.assertEqual(event_with_type_b_value.attr1, "blah")

    def test_evt_type_one_attr_union_type_tp_not_in_union(self):
        edef = src.events.get_event_def(self.evt_union)
        self.assertRaises(
            TypeError,
            edef,
            attr1=bytearray(3)
        )

    def test_evt_type_optional_one_attr_no_attr_given(self):
        edef = src.events.get_event_def(self.evt_optional)
        result = edef()
        self.assertFalse(hasattr(result, "attr1"))

    def test_evt_type_optional_one_attr_attr_given(self):
        edef = src.events.get_event_def(self.evt_optional)
        result = edef(attr1=2)
        self.assertEqual(result.attr1, 2)

    def test_evt_type_optional_wrong_type(self):
        edef = src.events.get_event_def(self.evt_optional)
        self.assertRaises(
            TypeError,
            edef,
            attr1=3.5
        )
