# Movie Library Metadata

You can have the script edit the metadata of Movies by adding them to the `metadata` mapping of a Metadata File.

An example of multiple metadata edits in a movie library is below:
```yaml
metadata:
  Godzilla (1954):
    title: Godzilla
    year: 1954
    content_rating: R
  Godzilla (1998):
    title: Godzilla
    year: 1998
    sort_title: Godzilla 03
    content_rating: PG-13
  Shin Godzilla:
    sort_title: Godzilla 06
    content_rating: R
  Godzilla 1985:
    content_rating: PG
  "Godzilla 2000: Millennium":
    originally_available: 1999-08-18
  Godzilla Against MechaGodzilla:
    originally_available: 2002-03-23
  Godzilla Raids Again:
    content_rating: G
    originally_available: 1955-05-21
  Godzilla vs. Biollante:
    content_rating: PG
  Godzilla vs. Destoroyah:
    content_rating: PG
    originally_available: 1995-01-19
  Godzilla vs. Gigan:
    content_rating: G
    originally_available: 1972-09-14
  Godzilla vs. Hedorah:
    content_rating: G
    originally_available: 1971-04-01
  Godzilla vs. King Ghidorah:
    content_rating: PG
    originally_available: 1991-04-28
  Godzilla vs. Mechagodzilla:
    content_rating: G
    originally_available: 1974-03-24
  Godzilla vs. Mechagodzilla II:
    content_rating: PG
  Godzilla vs. Megaguirus:
    content_rating: PG
    originally_available: 2000-08-31
  Godzilla vs. Megalon:
    content_rating: G
    originally_available: 1973-03-17
  Godzilla vs. Mothra:
    content_rating: PG
    originally_available: 1992-04-28
  Godzilla vs. SpaceGodzilla:
    content_rating: PG
    originally_available: 1994-01-19
  Godzilla, King of the Monsters!:
    content_rating: G
  "Godzilla, Mothra and King Ghidorah: Giant Monsters All-Out Attack":
    content_rating: PG
    originally_available: 2001-08-31
  "Godzilla: Final Wars":
    content_rating: PG
    originally_available: 2004-12-13
  "Godzilla: Tokyo S.O.S.":
    originally_available: 2003-12-14
  Halloween (Rob Zombie):
    alt_title: Halloween
    year: 2007
  "Halo 4: Forward Unto Dawn":
    alt_title: Halo 4 Forward Unto Dawn
    tmdb_show: 56295
    content_rating: R
```

## Movies

Each movie is defined by the mapping name which must be the same as the movie name in the library unless an `alt_title` is specified.

## Metadata Edits

The available attributes for editing movies are as follows

### Special Attributes

| Attribute    | Allowed Values                                                                                    |
|:-------------|:--------------------------------------------------------------------------------------------------|
| `title`      | Title if different from the mapping value useful when you have multiple movies with the same name |
| `alt_title`  | Alternative title to look for                                                                     |
| `year`       | Year of movie for better identification                                                           |
| `tmdb_show`  | TMDb Show ID to use for metadata useful for miniseries that have been compiled into a movie       |
| `tmdb_movie` | TMDb Movie ID to use for metadata useful for movies that have been split into segments            |


* YAML files cannot have two items with the same mapping name so if you have two movies with the same name you would change the mapping values to whatever you want. Then use the `title` attribute to specify the real title and use the `year` attribute to specify which of the multiple movies to choose.
    ```yaml
    metadata:
      Godzilla1:
        title: Godzilla
        year: 1954
        content_rating: R
      Godzilla2:
        title: Godzilla
        year: 1998
        content_rating: PG-13
    ```

* If you know of another Title your movie might exist under, but you want it titled differently you can use `alt_title` to specify another title to look under and then be changed to the mapping name. For Example TMDb uses the name `The Legend of Korra`, but I want it as `Avatar: The Legend of Korra` (Which must be surrounded by quotes since it uses the character `:`):
    ```yaml
    metadata:
      "Avatar: The Legend of Korra":
        alt_title: The Legend of Korra
    ```
    This would change the name of the TMDb default `The Legend of Korra` to `Avatar: The Legend of Korra` and would not mess up any subsequent runs.

### General Attributes

| Attribute              | Allowed Values                                                |
|:-----------------------|:--------------------------------------------------------------|
| `sort_title`           | Text to change Sort Title                                     |
| `original_title`       | Text to change Original Title                                 |
| `originally_available` | Date to change Originally Available<br>**Format:** YYYY-MM-DD |
| `content_rating`       | Text to change Content Rating                                 |
| `user_rating`          | Number to change User Rating                                  |
| `audience_rating`      | Number to change Audience Rating                              |
| `critic_rating`        | Number to change Critic Rating                                |
| `studio`               | Text to change Studio                                         |
| `tagline`              | Text to change Tagline                                        |
| `summary`              | Text to change Summary                                        |

### Tag Attributes

You can add `.remove` to any tag attribute to only remove those tags i.e. `genre.remove`.

You can add `.sync` to any tag attribute to sync all tags vs just appending the new ones i.e. `genre.sync`.

| Attribute    | Allowed Values                                      |
|:-------------|:----------------------------------------------------|
| `director`   | List or comma-separated text of each Director Tag   |
| `country`    | List or comma-separated text of each Country Tag    |
| `genre`      | List or comma-separated text of each Genre Tag      |
| `writer`     | List or comma-separated text of each Writer Tag     |
| `producer`   | List or comma-separated text of each Producer Tag   |
| `collection` | List or comma-separated text of each Collection Tag |
| `label`      | List or comma-separated text of each Label Tag      |

### Advanced Attributes

| Attribute            | Allowed Values                                                                                                                                                                                                                                                                                                                                                                                      |
|:---------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `metadata_language`  | `default`, `ar-SA`, `ca-ES`, `cs-CZ`, `da-DK`, `de-DE`, `el-GR`, `en-AU`, `en-CA`, `en-GB`, `en-US`, `es-ES`, `es-MX`, `et-EE`, `fa-IR`, `fi-FI`, `fr-CA`, `fr-FR`, `he-IL`, `hi-IN`, `hu-HU`, `id-ID`, `it-IT`, `ja-JP`, `ko-KR`, `lt-LT`, `lv-LV`, `nb-NO`, `nl-NL`, `pl-PL`, `pt-BR`, `pt-PT`, `ro-RO`, `ru-RU`, `sk-SK`, `sv-SE`, `th-TH`, `tr-TR`, `uk-UA`, `vi-VN`, `zh-CN`, `zh-HK`, `zh-TW` |
| `use_original_title` | `default`: Library default<br>`no`: No<br>`yes`: Yes                                                                                                                                                                                                                                                                                                                                                |

\* Must be using the **New Plex Movie Agent*

### Image Attributes

| Attribute         | Description                                                           | Allowed Values                                  |
|:------------------|:----------------------------------------------------------------------|:------------------------------------------------|
| `url_poster`      | Used to change the movie's poster to the URL                          | URL of image publicly available on the internet |
| `file_poster`     | Used to change the movie's poster to the image in the file system     | Path to image in the file system                |
| `url_background`  | Use to change the movie's background to the URL                       | URL of image publicly available on the internet |
| `file_background` | Used to change the movie's background to the image in the file system | Path to image in the file system                |
