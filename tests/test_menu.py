"""Tests for menu generation and routing patterns."""

from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup

import menu
import utils


def labels(markup):
    """Flatten reply keyboard labels."""
    return [button.text for row in markup.keyboard for button in row]


def test_root_menu(cache):  # pylint: disable=unused-argument
    """The root menu lists top level sections."""
    markup = menu.gen_menu(1)
    assert isinstance(markup, ReplyKeyboardMarkup)
    assert labels(markup) == list(utils.cfg)


def test_unknown_item_falls_back_to_root(cache):  # pylint: disable=unused-argument
    """Unknown labels show the root menu instead of an empty keyboard."""
    assert labels(menu.gen_menu(1, "nope")) == list(utils.cfg)


def test_submenu_and_back(cache):
    """Back returns to the parent of the current submenu."""
    monitoring, k8s = "💻 Monitoring", "🚢 K8S"
    assert utils.BACK_BUTTON in labels(menu.gen_menu(1, monitoring))
    menu.gen_menu(1, k8s)
    assert cache.data["state_1"] == {"current": k8s}
    menu.gen_menu(1, utils.BACK_BUTTON)
    assert cache.data["state_1"] == {"current": monitoring}


def test_back_without_state(cache):  # pylint: disable=unused-argument
    """Back without stored state shows the root menu."""
    assert labels(menu.gen_menu(1, utils.BACK_BUTTON)) == list(utils.cfg)


def test_leaf_shows_inline_buttons(cache):  # pylint: disable=unused-argument
    """A list of calls becomes inline buttons."""
    markup = menu.gen_menu(1, "🕸 Sites")
    assert isinstance(markup, InlineKeyboardMarkup)
    assert [row[0].callback_data for row in markup.inline_keyboard] == [
        "site_add", "site_del", "site_list", "site_info"]


def test_menu_pattern_matches_only_menu_labels():
    """Free text starting with symbols is not mistaken for a menu button."""
    pattern = utils.menu_pattern()
    assert pattern.match("💻 Monitoring")
    assert pattern.match(utils.BACK_BUTTON)
    assert not pattern.match("💻 Monitoring please")
    assert not pattern.match("例子.com")


def test_call_pattern_includes_new_tools():
    """New tools are routed to the button handler."""
    pattern = utils.call_pattern()
    for call in ("ssl_check", "api_rotate", "site_add"):
        assert pattern.match(call)
    assert not pattern.match("worker")
