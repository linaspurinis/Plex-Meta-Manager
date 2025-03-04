# Sonarr Attributes

Configuring [Sonarr](https://sonarr.tv/) is optional but will allow you to send shows to a Sonarr instance when they're found missing while updating a library's collections.

Sonarr V2 may work, but it is not supported please upgrade to V3 if you can.

Items in your List Exclusions will be ignored by PMM.

A `sonarr` mapping can be either in the root of the config file as global mapping for all libraries, or you can specify the `sonarr` mapping individually per library.

Below is a `sonarr` mapping example and the full set of attributes:
```YAML
sonarr:
  url: http://192.168.1.12:32789
  token: ################################
  add_missing: false
  add_existing: false
  root_folder_path: S:/Shows
  monitor: all
  quality_profile: HD-1080p
  language_profile: English
  series_type: standard
  season_folder: true
  tag: pmm
  search: false
  cutoff_search: false
  sonarr_path: /media
  plex_path: /share/CACHEDEV1_DATA/Multimedia
```

| Attribute          | Allowed Values                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |    Default    | Required |
|:-------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------:|:--------:|
| `url`              | Sonarr URL (Including URL Base if set).<br>**Example:** http://192.168.1.12:32788                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |      N/A      | &#9989;  |
| `token`            | Sonarr API Token.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |      N/A      | &#9989;  |
| `add_missing`      | Adds all missing shows found from all collections to Sonarr.<br>Use the `sonarr_add_missing` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to add missing per collection.<br>**boolean:** true or false                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |     false     | &#10060; |
| `add_existing`     | Adds all existing shows in collections to Sonarr.<br>Use the `sonarr_add_existing` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to add existing per collection.<br>**boolean:** true or false                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |     false     | &#10060; |
| `root_folder_path` | Default Root Folder Path to use when adding new shows.<br>Use the `sonarr_folder` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the Root Folder per collection.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |      N/A      | &#9989;  |
| `monitor`          | Default Monitor to use when adding new shows.<br>Use the `sonarr_monitor` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the Monitor value per collection.<br>**Values:** <table class="clearTable"><tr><td>`all`</td><td>All episodes except specials</td></tr><tr><td>`future`</td><td>Episodes that have not aired yet</td></tr><tr><td>`missing`</td><td>Episodes that do not have files or have not aired yet</td></tr><tr><td>`existing`</td><td>Episodes that have files or have not aired yet</td></tr><tr><td>`pilot`</td><td>The first episode, all others will be ignored</td></tr><tr><td>`first`</td><td>All episodes of the first season, all others will be ignored</td></tr><tr><td>`latest`</td><td>All episodes of the latest season and future seasons</td></tr><tr><td>`none`</td><td>No episodes</td></tr></table> |     `all`     | &#10060; |
| `quality_profile`  | Default Quality Profile to use when adding new shows.<br>Use the `sonarr_quality` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the Quality Profile per collection.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |      N/A      | &#9989;  |
| `language_profile` | Default Language Profile to use when adding new shows.<br>Use the `sonarr_language` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the Language Profile per collection.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | First Profile | &#10060; |
| `series_type`      | Default Series Type to use when adding new shows.<br>Use the `sonarr_series` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the Series Type per collection.<br>**Values:** <table class="clearTable"><tr><td>`standard`</td><td>Episodes released with SxxEyy pattern</td></tr><tr><td>`daily`</td><td>Episodes released daily that use year-month-day pattern (2017-05-25)</td></tr><tr><td>`anime`</td><td>Episodes released using an absolute episode number</td></tr></table>`standard`: Episodes released with SxxEyy pattern<br>`daily`: Episodes released daily or less frequently that use year-month-day (2017-05-25)<br>`anime`: Episodes released using an absolute episode number                                                                                                                                           |  `standard`   | &#10060; |
| `season_folder`    | Use the Season Folder Option when adding new shows.<br>Use the `sonarr_season` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the season folder value per collection. <br>**boolean:** true or false                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |     true      | &#10060; |
| `tag`              | Default this list or comma-separated string of tags to use when adding new shows.<br>Use the `sonarr_tag` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the tags per collection.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |      ` `      | &#10060; |
| `search`           | Start search for missing episodes when adding new shows.<br>Use the `sonarr_search` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the search value per collection.<br>**boolean:** true or false                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |     false     | &#10060; |
| `cutoff_search`    | Start search for cutoff unmet episodes when adding new shows.<br>Use the `sonarr_cutoff_search` [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition to set the cutoff search value per collection.<br>**boolean:** true or false                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |     false     | &#10060; |
| `plex_path`        | When using `add_existing` or `sonarr_add_all` Convert this part of the path to `sonarr_path`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |      ` `      | &#10060; |
| `sonarr_path`      | When using `add_existing` or `sonarr_add_all` Convert the `plex_path` part of the path to this.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |      ` `      | &#10060; |

* The `token` can be found by going to `Sonarr > Settings > General > Security > API Key`

* The `quality_profile` and `language_profile` must be the exact name of the desired quality profile, including all spaces and capitalization.

* You can set most attributes per collection by using the [Sonarr Details](../metadata/details/arr.md#sonarr-details) in the collection definition.

![Sonarr Details](sonarr.png)

# Other examples:

Specifying a second Sonarr instance for a specific library:

In this example we have two Sonarr instances, standard and 4K.  We want to add 4K shows to the 4K Sonarr instance with a different root folder and quality profile.  Also, shows are being added to the "TV Shows - 4K" library outside Sonarr via a custom script and I want those new shows added to Sonarr for tracking.

```yaml
libraries:
  TV Shows:
    metadata_path:
      - file: config/TV.yml
  TV Shows - 4K:
    metadata_path:
      - file: config/TV.yml
    sonarr:
      url: https://sonarr-4K.bing.bang
      token: SOME_TOKEN
      root_folder_path: /shows-4K
      quality_profile: 4K
      add_existing: true
      sonarr_path: /shows-4K
      plex_path: /mnt/unionfs/Media/TV
...
sonarr:
  url: https://sonarr.bing.bang
  token: SOME_TOKEN
  add_missing: false
  add_existing: false
  root_folder_path: /shows
  monitor: all
  quality_profile: HD-1080p
  language_profile: English
  series_type: standard
  season_folder: true
  tag:
  search: false
  cutoff_search: false
  sonarr_path:
  plex_path:
...
```
