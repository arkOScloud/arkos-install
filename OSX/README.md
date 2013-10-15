## How to translate the Installer

### For Translators

If you cannot code but you just want to help by translating it in your language, then ask a developer for the english template file for translations. Once you have it you can open it and edit it with a text editor (feel free to look at the already completed translations to get an idea of how they must be structured) and when you are done just send the file back to one of the developers.

### For Developers

If you are a developer first you should install the `gettext` terminal utilities. I suggest that you install them from source (the Homebrew formula apparently doesn't give you the full package with all the utilities needed). Here is a link to the [official webpage of the project](https://www.gnu.org/software/gettext/).

The translations are all located in `arkos-install/translations`. Their extension is `.po`. to be used by the application they must be first compiled with the `msgfmt` command, that will generate an `.mo` file.

To generate an empty `.po` file with all the english strings ready for translation just go to `arkos-install` and launch `xgettext Installer.py --language=Python`.

## Distribution

When you want to distribute the installer then you should first compile all the `.po` files and then delete them (a simple automation script will be added as soon as possible). Afterwards launch `python setup.py py2app`in the main directory and a nice executable will be generated in `dist`.