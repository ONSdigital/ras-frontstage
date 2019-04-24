# Useful scripts for Frontstage Development

Shell scripts that you may find useful for development on Frontstage:

## `get_strings.py` - generate JSON of strings in a file for extraction into a language file

Usage:

```
$ python get_strings.py [filename]
```

Searches the file for strings wrapped with the substitution function `_([string])`, and returns JSON that can be copied into a language file.

**NB: Output is the content of a locale, but doesn't include the locale itself, because we don't know which locale you need.**

Typically, the output should be copied into a strings file in `frontstage/i18n` and in the format below:

```json
{
    "[LOCALEKEY]": [PASTED CONTENT HERE]
}
```

If you have multiple locale sets, then you would need to paste the output in multiple times:

```json
{
    "[LOCALEKEY1": [PASTED CONTENT HERE],
    "[LOCALEKEY2": [PASTED CONTENT HERE AS WELL]
}
```

You then change any strings that you want to change, either for replacement, or for translation purposes.  Any you don't want to change should remain `false` or should be removed from the list.

You can also use this file to send to someone else to define what the strings should say.

Locale keys are in the form below:

`[LANGUAGE CODE]_[COUNTRY CODE]`

See examples below:

| Country         | Country code |
|-----------------|--------------|
| Great Britain   | en_GB        |
| USA             | en_US        |
| France          | fr_FR        |

Note that the language code is always lowercase, and the country code always uppercase.

As a final example, the below shows a JSON language file that contains the same entries, with same overrides for US English:

```json
{
    "en_GB": {
        "What is your favourite colour?": false,
        "What brand of nappy do you buy for your baby?": false
    },
    "en_US": {
        "What is your favourite colour?": "What is your favorite color?",
        "What brand of nappy do you buy for your baby?": "What brand of diaper do you buy for your baby?"
    }
}
```

In the above:
* The British English strings remain as specified in source code
* The American English strings are overridden with American English terms and spellings.

Locales use the Python locale setting, which we will have to introduce mechanisms to change if this feature is used.  **Translation is not the intended purpose of this system, but it was easy to make a step toward allowing it within this string extraction mechanism**