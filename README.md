# Screenshots for QGIS

Derived from https://github.com/boundlessgeo/qgis-lessons-plugin with the ambition of automating taking screenshots to help keep documentation up to date.


## Installation

`pip install --target=${HOME}.local/share/QGIS/QGIS3/profiles/default/python/plugins/screenshots/extlibs -r requirements.txt`

### Devlopment environment notes

After you've cloned this repository you can create a symlink from the plugin directory (`qgis-screenshots-plugin/screenshots/`) to where the QGIS plugin directory.

    `ln -s path/to/dev/folder/qgis-screenshots-plugin/screenshots/ ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/screenshots`
