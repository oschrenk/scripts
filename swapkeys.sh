#!/bin/bash
# The script is intended to automatically switch the keybindings of
# special keys on OSX which is normally done through
# System Preferences -> Keybopard > Modifier keys

# This Script does NOT work, see
# http://forums.macrumors.com/showthread.php?t=949280
# http://apple.stackexchange.com/questions/13598/updating-modifier-key-mappings-through-defaults-command-tool

mappingplist=com.apple.keyboard.modifiermapping.1452-545-0

if [ $1 == "emacs" ]; then
    echo "Switching to emacs modifiers"
    defaults -currentHost write -g $mappingplist '(
                {
            HIDKeyboardModifierMappingDst = 4;
            HIDKeyboardModifierMappingSrc = 2; },
                {
            HIDKeyboardModifierMappingDst = 12;
            HIDKeyboardModifierMappingSrc = 10;
        },
                {
            HIDKeyboardModifierMappingDst = 2;
            HIDKeyboardModifierMappingSrc = 4;
        },
                {
            HIDKeyboardModifierMappingDst = 10;
            HIDKeyboardModifierMappingSrc = 12;
        })'


else
    echo "Switching to default modifiers"
    defaults -currentHost delete -g $mappingplist
fi