""" Settings and GUISettings tests """
import os
import json
from unittest import TestCase, mock

from ytsm.settings import Settings, GUISettings, GUIColorScheme, GUIFontScheme, CLISettings

class TestSettings(TestCase):
    def setUp(self) -> None:
        """ Setup for settings tests """
        self.settings = Settings()

    def test_set_path(self):
        self.assertEqual(None, self.settings.path)  # Empty by default
        self.settings.set_path('Test')
        self.assertEqual('Test', self.settings.path)

    def test_load_settings(self):
        with open('test.json', 'w', encoding='utf-8') as w_file:
            json.dump(self.settings.__dict__(), w_file)

        # No tuples on JSON!
        self.settings.gui_settings.default_window_size = \
            [self.settings.gui_settings.default_window_size[0],
             self.settings.gui_settings.default_window_size[1]]

        new_settings = Settings()
        new_settings.path = 'test.json'
        new_settings.gui_settings = None  # Alter new_settings to check loading
        new_settings.load_settings()
        self.assertEqual(self.settings.__dict__(), new_settings.__dict__())

        # Clean
        os.remove('test.json')

    def test_load_settings_raises_SettingsHasNoPath(self):
        self.assertRaises(Settings.SettingsHasNoPath, self.settings.load_settings)

    def test_load_settings_raises_BrokenJSON(self):
        with open('test.json', 'w', encoding='utf-8') as w_file:
            w_file.write('{')

        self.settings.path = 'test.json'
        self.assertRaises(Settings.BrokenJSONFile, self.settings.load_settings)

        # Clean
        os.remove('test.json')

    def test_load_settings_raises_ExtraKeys(self):
        self.settings.path = 'test.json'
        self.settings.save_settings()
        with open('test.json', 'r', encoding='utf-8') as r_file:
            json_file = json.load(r_file)
        json_file['gui_settings']['extra_key'] = 666

        with open('test.json', 'w', encoding='utf-8') as w_file:
            json.dump(json_file, w_file)

        self.assertRaises(Settings.ExtraKeys, self.settings.load_settings)

        # Clean
        os.remove('test.json')

    def test_save_settings(self):
        self.settings.set_path('test.json')
        self.settings.gui_settings.fontscheme.normal_size = 666
        self.settings.save_settings()

        with open('test.json', 'r', encoding='utf-8') as r_file:
            json_file = json.load(r_file)

        # No tuples on JSON!
        self.settings.gui_settings.default_window_size = \
            [self.settings.gui_settings.default_window_size[0],
             self.settings.gui_settings.default_window_size[1]]

        self.assertEqual(self.settings.__dict__(), json_file)

        # Clean
        os.remove('test.json')

    def test_save_settings_raises_SettingsHasNoPath(self):
        self.assertRaises(Settings.SettingsHasNoPath, self.settings.save_settings)

    @mock.patch("ytsm.settings.Settings.save_settings")
    def test_restore_settings_no_type(self, mocked_func):
        # No type
        self.settings.gui_settings = None
        self.settings.cli_settings = None
        self.settings.restore_settings()
        mocked_func.assert_called()
        self.assertEqual(GUISettings(), self.settings.gui_settings)
        self.assertEqual(CLISettings(), self.settings.cli_settings)

    @mock.patch("ytsm.settings.Settings.save_settings")
    def test_restore_settings_gui_settings(self, mocked_func):
        # GUISettings only
        self.settings.gui_settings = None
        self.settings.cli_settings = None
        self.settings.restore_settings(restore_type=GUISettings)
        mocked_func.assert_called()
        self.assertEqual(GUISettings(), self.settings.gui_settings)
        self.assertEqual(None, self.settings.cli_settings)

    @mock.patch("ytsm.settings.Settings.save_settings")
    def test_restore_settings_cli_settings(self, mocked_func):
        # CLISettings only
        self.settings.gui_settings = None
        self.settings.cli_settings = None
        self.settings.restore_settings(restore_type=CLISettings)
        mocked_func.assert_called()
        self.assertEqual(None, self.settings.gui_settings)
        self.assertEqual(CLISettings(), self.settings.cli_settings)

    def test_restore_settings_raises_TypeError(self):
        self.assertRaises(TypeError, self.settings.restore_settings, restore_type=int)

class TestGUISettings(TestCase):
    def test_to_json(self):
        gs = GUISettings()
        expected = gs.__dict__ | {'colorscheme': GUIColorScheme().__dict__, 'fontscheme': GUIFontScheme().__dict__}
        self.assertEqual(expected, gs.to_json())
