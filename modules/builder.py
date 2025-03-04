import os, re, time
from datetime import datetime, timedelta
from modules import anidb, anilist, flixpatrol, icheckmovies, imdb, letterboxd, mal, plex, radarr, reciperr, sonarr, tautulli, tmdb, trakt, tvdb, mdblist, util
from modules.util import Failed, ImageData, NotScheduled, NotScheduledRange
from PIL import Image
from plexapi.audio import Artist, Album, Track
from plexapi.exceptions import BadRequest, NotFound
from plexapi.video import Movie, Show, Season, Episode
from urllib.parse import quote

logger = util.logger

advance_new_agent = ["item_metadata_language", "item_use_original_title"]
advance_show = ["item_episode_sorting", "item_keep_episodes", "item_delete_episodes", "item_season_display", "item_episode_sorting"]
method_alias = {
    "actors": "actor", "role": "actor", "roles": "actor",
    "show_actor": "actor", "show_actors": "actor", "show_role": "actor", "show_roles": "actor",
    "collections": "collection", "plex_collection": "collection",
    "show_collections": "collection", "show_collection": "collection",
    "content_ratings": "content_rating", "contentRating": "content_rating", "contentRatings": "content_rating",
    "countries": "country",
    "decades": "decade",
    "directors": "director",
    "genres": "genre",
    "labels": "label",
    "collection_minimum": "minimum_items",
    "playlist_minimum": "minimum_items",
    "rating": "critic_rating",
    "show_user_rating": "user_rating",
    "video_resolution": "resolution",
    "tmdb_trending": "tmdb_trending_daily",
    "play": "plays", "show_plays": "plays", "show_play": "plays", "episode_play": "episode_plays",
    "originally_available": "release", "episode_originally_available": "episode_air_date",
    "episode_release": "episode_air_date", "episode_released": "episode_air_date",
    "show_originally_available": "release", "show_release": "release", "show_air_date": "release",
    "released": "release", "show_released": "release", "max_age": "release",
    "studios": "studio",
    "networks": "network",
    "producers": "producer",
    "writers": "writer",
    "years": "year", "show_year": "year", "show_years": "year",
    "show_title": "title", "filter": "filters",
    "seasonyear": "year", "isadult": "adult", "startdate": "start", "enddate": "end", "averagescore": "score",
    "minimum_tag_percentage": "min_tag_percent", "minimumtagrank": "min_tag_percent", "minimum_tag_rank": "min_tag_percent",
    "anilist_tag": "anilist_search", "anilist_genre": "anilist_search", "anilist_season": "anilist_search",
    "mal_producer": "mal_studio", "mal_licensor": "mal_studio",
    "trakt_recommended": "trakt_recommended_weekly", "trakt_watched": "trakt_watched_weekly", "trakt_collected": "trakt_collected_weekly",
    "collection_changes_webhooks": "changes_webhooks",
    "radarr_add": "radarr_add_missing", "sonarr_add": "sonarr_add_missing",
    "trakt_recommended_personal": "trakt_recommendations"
}
filter_translation = {
    "record_label": "studio",
    "actor": "actors",
    "audience_rating": "audienceRating",
    "collection": "collections",
    "content_rating": "contentRating",
    "country": "countries",
    "critic_rating": "rating",
    "director": "directors",
    "genre": "genres",
    "label": "labels",
    "producer": "producers",
    "release": "originallyAvailableAt",
    "added": "addedAt",
    "last_played": "lastViewedAt",
    "plays": "viewCount",
    "user_rating": "userRating",
    "writer": "writers",
    "mood": "moods",
    "style": "styles"
}
modifier_alias = {".greater": ".gt", ".less": ".lt"}
all_builders = anidb.builders + anilist.builders + flixpatrol.builders + icheckmovies.builders + imdb.builders + \
               letterboxd.builders + mal.builders + plex.builders + reciperr.builders + tautulli.builders + \
               tmdb.builders + trakt.builders + tvdb.builders + mdblist.builders
show_only_builders = [
    "tmdb_network", "tmdb_show", "tmdb_show_details", "tvdb_show", "tvdb_show_details", "tmdb_airing_today",
    "tmdb_on_the_air", "collection_level", "item_tmdb_season_titles"
]
movie_only_builders = [
    "letterboxd_list", "letterboxd_list_details", "icheckmovies_list", "icheckmovies_list_details", "stevenlu_popular",
    "tmdb_collection", "tmdb_collection_details", "tmdb_movie", "tmdb_movie_details", "tmdb_now_playing",
    "tvdb_movie", "tvdb_movie_details", "tmdb_upcoming", "trakt_boxoffice", "reciperr_list"
]
music_only_builders = ["item_album_sorting"]
summary_details = [
    "summary", "tmdb_summary", "tmdb_description", "tmdb_biography", "tvdb_summary",
    "tvdb_description", "trakt_description", "letterboxd_description", "icheckmovies_description"
]
poster_details = ["url_poster", "tmdb_poster", "tmdb_profile", "tvdb_poster", "file_poster"]
background_details = ["url_background", "tmdb_background", "tvdb_background", "file_background"]
boolean_details = [
    "show_filtered", "show_missing", "save_missing", "missing_only_released", "only_filter_missing",
    "delete_below_minimum", "asset_folders", "create_asset_folders"
]
scheduled_boolean = ["visible_library", "visible_home", "visible_shared"]
string_details = ["sort_title", "content_rating", "name_mapping"]
ignored_details = [
    "smart_filter", "smart_label", "smart_url", "run_again", "schedule", "sync_mode", "template", "test",
    "delete_not_scheduled", "tmdb_person", "build_collection", "collection_order", "collection_level",
    "validate_builders", "libraries", "sync_to_users", "collection_name", "playlist_name", "name", "blank_collection"
]
details = [
    "ignore_ids", "ignore_imdb_ids", "server_preroll", "changes_webhooks", "collection_mode", "limit", "url_theme",
    "file_theme", "minimum_items", "label", "album_sorting", "cache_builders", "tmdb_region"
] + boolean_details + scheduled_boolean + string_details
collectionless_details = ["collection_order", "plex_collectionless", "label", "label_sync_mode", "test"] + \
                         poster_details + background_details + summary_details + string_details
item_false_details = ["item_lock_background", "item_lock_poster", "item_lock_title"]
item_bool_details = ["item_tmdb_season_titles", "item_assets", "revert_overlay", "item_refresh"] + item_false_details
item_details = ["non_item_remove_label", "item_label", "item_radarr_tag", "item_sonarr_tag", "item_overlay", "item_refresh_delay"] + item_bool_details + list(plex.item_advance_keys.keys())
none_details = ["label.sync", "item_label.sync"]
radarr_details = ["radarr_add_missing", "radarr_add_existing", "radarr_folder", "radarr_monitor", "radarr_search", "radarr_availability", "radarr_quality", "radarr_tag"]
sonarr_details = [
    "sonarr_add_missing", "sonarr_add_existing", "sonarr_folder", "sonarr_monitor", "sonarr_language", "sonarr_series",
    "sonarr_quality", "sonarr_season", "sonarr_search", "sonarr_cutoff_search", "sonarr_tag"
]
album_details = ["non_item_remove_label", "item_label", "item_album_sorting"]
discover_types = {
    "Documentary": "documentary", "News": "news", "Miniseries": "miniseries",
    "Reality": "reality", "Scripted": "scripted", "Talk Show": "talk_show", "Video": "video"
}
discover_status = {
    "Returning Series": "returning", "Planned": "planned", "In Production": "production",
    "Ended": "ended", "Canceled": "canceled", "Pilot": "pilot"
}
filters_by_type = {
    "movie_show_season_episode_artist_album_track": ["title", "summary", "collection", "has_collection", "added", "last_played", "user_rating", "plays"],
    "movie_show_season_episode_album_track": ["year"],
    "movie_show_episode_artist_track": ["filepath"],
    "movie_show_episode_album": ["release", "critic_rating", "history"],
    "movie_show_episode_track": ["duration"],
    "movie_show_artist_album": ["genre"],
    "movie_show_episode": ["actor", "content_rating", "audience_rating"],
    "movie_show_album": ["label"],
    "movie_episode_track": ["audio_track_title"],
    "movie_show": ["studio", "original_language", "has_overlay", "tmdb_vote_count", "tmdb_year", "tmdb_genre", "tmdb_title", "tmdb_keyword"],
    "movie_episode": ["director", "producer", "writer", "resolution", "audio_language", "subtitle_language", "has_dolby_vision"],
    "movie_artist": ["country"],
    "show": ["tmdb_status", "tmdb_type", "origin_country", "network", "first_episode_aired", "last_episode_aired"],
    "album": ["record_label"]
}
filters = {
    "movie": [item for check, sub in filters_by_type.items() for item in sub if "movie" in check],
    "show": [item for check, sub in filters_by_type.items() for item in sub if "show" in check],
    "season": [item for check, sub in filters_by_type.items() for item in sub if "season" in check],
    "episode": [item for check, sub in filters_by_type.items() for item in sub if "episode" in check],
    "artist": [item for check, sub in filters_by_type.items() for item in sub if "artist" in check],
    "album": [item for check, sub in filters_by_type.items() for item in sub if "album" in check],
    "track": [item for check, sub in filters_by_type.items() for item in sub if "track" in check]
}
tmdb_filters = [
    "original_language", "origin_country", "tmdb_vote_count", "tmdb_year", "tmdb_keyword", "tmdb_genre",
    "first_episode_aired", "last_episode_aired", "tmdb_status", "tmdb_type", "tmdb_title"
]
string_filters = ["title", "summary", "studio", "record_label", "filepath", "audio_track_title", "tmdb_title"]
string_modifiers = ["", ".not", ".is", ".isnot", ".begins", ".ends", ".regex"]
tag_filters = [
    "actor", "collection", "content_rating", "country", "director", "network", "genre", "label", "producer", "year", "origin_country",
    "writer", "original_language", "resolution", "audio_language", "subtitle_language", "tmdb_keyword", "tmdb_genre", "tmdb_status", "tmdb_type"
]
tag_modifiers = ["", ".not", ".count_gt", ".count_gte", ".count_lt", ".count_lte"]
boolean_filters = ["has_collection", "has_overlay", "has_dolby_vision"]
date_filters = ["release", "added", "last_played", "first_episode_aired", "last_episode_aired"]
date_modifiers = ["", ".not", ".before", ".after", ".regex"]
number_filters = ["year", "tmdb_year", "critic_rating", "audience_rating", "user_rating", "tmdb_vote_count", "plays", "duration"]
number_modifiers = [".gt", ".gte", ".lt", ".lte"]
special_filters = ["history"]
all_filters = boolean_filters + special_filters + \
              [f"{f}{m}" for f in string_filters for m in string_modifiers] + \
              [f"{f}{m}" for f in tag_filters for m in tag_modifiers] + \
              [f"{f}{m}" for f in date_filters for m in date_modifiers] + \
              [f"{f}{m}" for f in number_filters for m in number_modifiers]
smart_invalid = ["collection_order", "collection_level"]
smart_url_invalid = ["minimum_items", "filters", "run_again", "sync_mode", "show_filtered", "show_missing", "save_missing", "smart_label"] + radarr_details + sonarr_details
custom_sort_builders = [
    "plex_search", "plex_pilots", "tmdb_list", "tmdb_popular", "tmdb_now_playing", "tmdb_top_rated",
    "tmdb_trending_daily", "tmdb_trending_weekly", "tmdb_discover", "reciperr_list", "trakt_chart", "trakt_userlist",
    "tvdb_list", "imdb_chart", "imdb_list", "stevenlu_popular", "anidb_popular", "tmdb_upcoming", "tmdb_airing_today",
    "tmdb_on_the_air", "trakt_list", "trakt_watchlist", "trakt_collection", "trakt_trending", "trakt_popular", "trakt_boxoffice",
    "trakt_collected_daily", "trakt_collected_weekly", "trakt_collected_monthly", "trakt_collected_yearly", "trakt_collected_all",
    "flixpatrol_url", "flixpatrol_demographics", "flixpatrol_popular", "flixpatrol_top",
    "trakt_recommended_personal", "trakt_recommended_daily", "trakt_recommended_weekly", "trakt_recommended_monthly", "trakt_recommended_yearly", "trakt_recommended_all",
    "trakt_watched_daily", "trakt_watched_weekly", "trakt_watched_monthly", "trakt_watched_yearly", "trakt_watched_all",
    "tautulli_popular", "tautulli_watched", "mdblist_list", "letterboxd_list", "icheckmovies_list",
    "anilist_top_rated", "anilist_popular", "anilist_trending", "anilist_search", "anilist_userlist",
    "mal_all", "mal_airing", "mal_upcoming", "mal_tv", "mal_movie", "mal_ova", "mal_special",
    "mal_popular", "mal_favorite", "mal_suggested", "mal_userlist", "mal_season", "mal_genre", "mal_studio"
]
episode_parts_only = ["plex_pilots"]
parts_collection_valid = [
     "filters", "plex_all", "plex_search", "trakt_list", "trakt_list_details", "collection_mode", "label", "visible_library", "limit",
     "visible_home", "visible_shared", "show_missing", "save_missing", "missing_only_released", "server_preroll", "changes_webhooks",
     "item_lock_background", "item_lock_poster", "item_lock_title", "item_refresh", "item_refresh_delay", "imdb_list", "cache_builders",
     "url_theme", "file_theme"
] + episode_parts_only + summary_details + poster_details + background_details + string_details
playlist_attributes = [
    "filters", "name_mapping", "show_filtered", "show_missing", "save_missing",
    "missing_only_released", "only_filter_missing", "delete_below_minimum", "ignore_ids", "ignore_imdb_ids",
    "server_preroll", "changes_webhooks", "minimum_items", "cache_builders"
] + custom_sort_builders + summary_details + poster_details + radarr_details + sonarr_details
music_attributes = [
   "non_item_remove_label", "item_label", "item_assets", "item_lock_background", "item_lock_poster", "item_lock_title",
   "item_refresh", "item_refresh_delay", "plex_search", "plex_all", "filters"
] + details + summary_details + poster_details + background_details

class CollectionBuilder:
    def __init__(self, config, metadata, name, no_missing, data, library=None):
        self.config = config
        self.metadata = metadata
        self.mapping_name = name
        self.no_missing = no_missing
        self.data = data
        self.library = library
        self.libraries = []
        self.playlist = library is None
        methods = {m.lower(): m for m in self.data}
        self.type = "playlist" if self.playlist else "collection"
        self.Type = self.type.capitalize()

        if "name" in methods:
            name = self.data[methods["name"]]
        elif f"{self.type}_name" in methods:
            logger.warning(f"Config Warning: Running {self.type}_name as name")
            name = self.data[methods[f"{self.type}_name"]]
        else:
            name = None

        if name:
            logger.debug("")
            logger.debug("Validating Method: name")
            if not name:
                raise Failed(f"{self.Type} Error: name attribute is blank")
            logger.debug(f"Value: {name}")
            self.name = str(name)
        else:
            self.name = str(self.mapping_name)

        if "template" in methods:
            logger.debug("")
            logger.debug("Validating Method: template")
            new_attributes = self.metadata.apply_template(self.name, self.data, self.data[methods["template"]])
            for attr in new_attributes:
                if attr.lower() not in methods:
                    self.data[attr] = new_attributes[attr]
                    methods[attr.lower()] = attr

        if self.playlist:
            if "libraries" in methods:
                logger.debug("")
                logger.debug("Validating Method: libraries")
                if not self.data[methods["libraries"]]:
                    raise Failed(f"{self.Type} Error: libraries attribute is blank")
                else:
                    logger.debug(f"Value: {self.data[methods['libraries']]}")
                    for pl_library in util.get_list(self.data[methods["libraries"]]):
                        if str(pl_library) in config.library_map:
                            self.libraries.append(config.library_map[pl_library])
                        else:
                            raise Failed(f"Playlist Error: Library: {pl_library} not defined")
                    self.library = self.libraries[0]
            else:
                raise Failed("Playlist Error: libraries attribute is required")
        else:
            self.libraries.append(self.library)

        self.language = self.library.Plex.language
        self.details = {
            "show_filtered": self.library.show_filtered,
            "show_options": self.library.show_options,
            "show_missing": self.library.show_missing,
            "save_missing": self.library.save_missing,
            "missing_only_released": self.library.missing_only_released,
            "only_filter_missing": self.library.only_filter_missing,
            "asset_folders": self.library.asset_folders,
            "create_asset_folders": self.library.create_asset_folders,
            "delete_below_minimum": self.library.delete_below_minimum,
            "delete_not_scheduled": self.library.delete_not_scheduled,
            "changes_webhooks": self.library.changes_webhooks,
            "cache_builders": 0
        }
        self.item_details = {}
        self.radarr_details = {}
        self.sonarr_details = {}
        self.missing_movies = []
        self.missing_shows = []
        self.missing_parts = []
        self.added_to_radarr = []
        self.added_to_sonarr = []
        self.builders = []
        self.filters = []
        self.tmdb_filters = []
        self.added_items = []
        self.filtered_keys = {}
        self.run_again_movies = []
        self.run_again_shows = []
        self.notification_additions = []
        self.notification_removals = []
        self.items = []
        self.remove_item_map = {}
        self.posters = {}
        self.backgrounds = {}
        self.summaries = {}
        self.schedule = ""
        self.limit = 0
        self.beginning_count = 0
        self.minimum = self.library.minimum_items
        self.tmdb_region = None
        self.ignore_ids = [i for i in self.library.ignore_ids]
        self.ignore_imdb_ids = [i for i in self.library.ignore_imdb_ids]
        self.server_preroll = None
        self.current_time = datetime.now()
        self.current_year = self.current_time.year
        self.url_theme = None
        self.file_theme = None
        self.collection_poster = None
        self.collection_background = None
        self.exists = False
        self.created = False
        self.deleted = False
        self.sync_to_users = None
        self.valid_users = []

        if self.playlist:
            server_check = None
            for pl_library in self.libraries:
                if server_check:
                    if pl_library.PlexServer.machineIdentifier != server_check:
                        raise Failed("Playlist Error: All defined libraries must be on the same server")
                else:
                    server_check = pl_library.PlexServer.machineIdentifier

            self.sync_to_users = config.general["playlist_sync_to_users"]
            if "sync_to_users" in methods or "sync_to_user" in methods:
                s_attr = f"sync_to_user{'s' if 'sync_to_users' in methods else ''}"
                logger.debug("")
                logger.debug("Validating Method: sync_to_users")
                if self.data[methods[s_attr]]:
                    logger.warning(f"Playlist Error: sync_to_users attribute is blank defaulting to playlist_sync_to_user: {self.sync_to_users}")
                else:
                    logger.debug(f"Value: {self.data[methods[s_attr]]}")
                    self.sync_to_users = self.data[methods[s_attr]]
            else:
                logger.warning(f"Playlist Error: sync_to_users attribute not found defaulting to playlist_sync_to_user: {self.sync_to_users}")

            plex_users = self.library.users
            if self.sync_to_users:
                if str(self.sync_to_users) == "all":
                    self.valid_users = plex_users
                else:
                    for user in util.get_list(self.sync_to_users):
                        if user in plex_users:
                            self.valid_users.append(user)
                        else:
                            raise Failed(f"Playlist Error: User: {user} not found in plex\nOptions: {plex_users}")

        if "delete_not_scheduled" in methods:
            logger.debug("")
            logger.debug("Validating Method: delete_not_scheduled")
            logger.debug(f"Value: {data[methods['delete_not_scheduled']]}")
            self.details["delete_not_scheduled"] = util.parse(self.Type, "delete_not_scheduled", self.data, datatype="bool", methods=methods, default=False)

        if "schedule" in methods and not self.config.requested_collections:
            logger.debug("")
            logger.debug("Validating Method: schedule")
            if not self.data[methods["schedule"]]:
                raise Failed(f"{self.Type} Error: schedule attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['schedule']]}")
                err = None
                try:
                    util.schedule_check("schedule", self.data[methods['schedule']], self.current_time, self.config.run_hour)
                except NotScheduledRange as e:
                    err = e
                except NotScheduled as e:
                    if not self.config.ignore_schedules:
                        err = e
                if err:
                    suffix = ""
                    if self.details["delete_not_scheduled"]:
                        try:
                            self.obj = self.library.get_playlist(self.name) if self.playlist else self.library.get_collection(self.name)
                            logger.info(self.delete())
                            self.deleted = True
                            suffix = f" and was deleted"
                        except Failed:
                            suffix = f" and could not be found to delete"
                    raise NotScheduled(f"{err}\n\n{self.Type} {self.name} not scheduled to run{suffix}")

        self.collectionless = "plex_collectionless" in methods and not self.playlist

        self.validate_builders = True
        if "validate_builders" in methods:
            logger.debug("")
            logger.debug("Validating Method: validate_builders")
            logger.debug(f"Value: {data[methods['validate_builders']]}")
            self.validate_builders = util.parse(self.Type, "validate_builders", self.data, datatype="bool", methods=methods, default=True)

        self.run_again = False
        if "run_again" in methods:
            logger.debug("")
            logger.debug("Validating Method: run_again")
            logger.debug(f"Value: {data[methods['run_again']]}")
            self.run_again = util.parse(self.Type, "run_again", self.data, datatype="bool", methods=methods, default=False)

        self.build_collection = True
        if "build_collection" in methods and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: build_collection")
            logger.debug(f"Value: {data[methods['build_collection']]}")
            self.build_collection = util.parse(self.Type, "build_collection", self.data, datatype="bool", methods=methods, default=True)

        self.blank_collection = False
        if "blank_collection" in methods and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: blank_collection")
            logger.debug(f"Value: {data[methods['blank_collection']]}")
            self.blank_collection = util.parse(self.Type, "blank_collection", self.data, datatype="bool", methods=methods, default=False)

        self.sync = self.library.sync_mode == "sync"
        if "sync_mode" in methods:
            logger.debug("")
            logger.debug("Validating Method: sync_mode")
            if not self.data[methods["sync_mode"]]:
                logger.warning(f"Collection Warning: sync_mode attribute is blank using general: {self.library.sync_mode}")
            else:
                logger.debug(f"Value: {self.data[methods['sync_mode']]}")
                if self.data[methods["sync_mode"]].lower() not in ["append", "sync"]:
                    logger.warning(f"Collection Warning: {self.data[methods['sync_mode']]} sync_mode invalid using general: {self.library.sync_mode}")
                else:
                    self.sync = self.data[methods["sync_mode"]].lower() == "sync"

        if self.playlist:               self.collection_level = "item"
        elif self.library.is_show:      self.collection_level = "show"
        elif self.library.is_music:     self.collection_level = "artist"
        else:                           self.collection_level = "movie"
        if "collection_level" in methods and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: collection_level")
            if self.library.is_movie:
                raise Failed(f"{self.Type} Error: collection_level attribute only works for show and music libraries")
            elif self.data[methods["collection_level"]] is None:
                raise Failed(f"{self.Type} Error: collection_level attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['collection_level']]}")
                if (self.library.is_show and self.data[methods["collection_level"]].lower() in plex.collection_level_show_options) or \
                        (self.library.is_music and self.data[methods["collection_level"]].lower() in plex.collection_level_music_options):
                    self.collection_level = self.data[methods["collection_level"]].lower()
                else:
                    if self.library.is_show:
                        options = "\n\tseason (Collection at the Season Level)\n\tepisode (Collection at the Episode Level)"
                    else:
                        options = "\n\talbum (Collection at the Album Level)\n\ttrack (Collection at the Track Level)"
                    raise Failed(f"{self.Type} Error: {self.data[methods['collection_level']]} collection_level invalid{options}")
        self.parts_collection = self.collection_level in plex.collection_level_options

        if "tmdb_person" in methods:
            logger.debug("")
            logger.debug("Validating Method: tmdb_person")
            if not self.data[methods["tmdb_person"]]:
                raise Failed(f"{self.Type} Error: tmdb_person attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['tmdb_person']]}")
                valid_names = []
                for tmdb_id in util.get_int_list(self.data[methods["tmdb_person"]], "TMDb Person ID"):
                    person = self.config.TMDb.get_person(tmdb_id)
                    valid_names.append(person.name)
                    if person.biography:
                        self.summaries["tmdb_person"] = person.biography
                    if person.profile_url:
                        self.posters["tmdb_person"] = person.profile_url
                if len(valid_names) > 0:
                    self.details["tmdb_person"] = valid_names
                else:
                    raise Failed(f"{self.Type} Error: No valid TMDb Person IDs in {self.data[methods['tmdb_person']]}")

        self.smart_filter_details = ""
        self.smart_label = {"sort_by": "random", "all": {"label": self.name}}
        self.smart_label_collection = False
        if "smart_label" in methods and not self.playlist and not self.library.is_music:
            logger.debug("")
            logger.debug("Validating Method: smart_label")
            self.smart_label_collection = True
            if not self.data[methods["smart_label"]]:
                logger.warning(f"{self.Type} Error: smart_label attribute is blank defaulting to random")
            else:
                logger.debug(f"Value: {self.data[methods['smart_label']]}")
                if isinstance(self.data[methods["smart_label"]], dict):
                    _data, replaced = util.replace_label(self.name, self.data[methods["smart_label"]])
                    if not replaced:
                        raise Failed("Config Error: <<smart_label>> not found in the smart_label attribute data")
                    self.smart_label = _data
                elif (self.library.is_movie and str(self.data[methods["smart_label"]]).lower() in plex.movie_sorts) \
                        or (self.library.is_show and str(self.data[methods["smart_label"]]).lower() in plex.show_sorts):
                    self.smart_label["sort_by"] = str(self.data[methods["smart_label"]]).lower()
                else:
                    logger.warning(f"{self.Type} Error: smart_label attribute: {self.data[methods['smart_label']]} is invalid defaulting to random")
        if self.smart_label_collection and self.library.smart_label_check(self.name):
            _, self.smart_filter_details, _ = self.build_filter("smart_label", self.smart_label, default_sort="random")

        self.smart_url = None
        self.smart_type_key = None
        if "smart_url" in methods and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: smart_url")
            if not self.data[methods["smart_url"]]:
                raise Failed(f"{self.Type} Error: smart_url attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['smart_url']]}")
                try:
                    self.smart_url, self.smart_type_key = self.library.get_smart_filter_from_uri(self.data[methods["smart_url"]])
                except ValueError:
                    raise Failed(f"{self.Type} Error: smart_url is incorrectly formatted")

        if "smart_filter" in methods and not self.playlist:
            self.smart_type_key, self.smart_filter_details, self.smart_url = self.build_filter("smart_filter", self.data[methods["smart_filter"]], display=True, default_sort="random")

        if self.collectionless:
            for x in ["smart_label", "smart_filter", "smart_url"]:
                if x in methods:
                    self.collectionless = False
                    logger.info("")
                    logger.warning(f"{self.Type} Error: {x} is not compatible with plex_collectionless removing plex_collectionless")

        if self.run_again and self.smart_url:
            self.run_again = False
            logger.info("")
            logger.warning(f"{self.Type} Error: smart_filter is not compatible with run_again removing run_again")

        if self.smart_url and self.smart_label_collection:
            raise Failed(f"{self.Type} Error: smart_filter is not compatible with smart_label")

        if self.parts_collection:
            for x in ["smart_label", "smart_filter", "smart_url"]:
                if x in methods:
                    raise Failed(f"{self.Type} Error: {x} is not compatible with collection_level: {self.collection_level}")

        self.smart = self.smart_url or self.smart_label_collection

        test_sort = None
        if "collection_order" in methods and not self.playlist and self.build_collection:
            if self.data[methods["collection_order"]] is None:
                raise Failed(f"{self.Type} Warning: collection_order attribute is blank")
            else:
                test_sort = self.data[methods["collection_order"]]
        elif "collection_order" not in methods and not self.playlist and self.build_collection and self.library.default_collection_order and not self.smart:
            test_sort = self.library.default_collection_order
            logger.warning("")
            logger.warning(f"{self.Type} Warning: collection_order not found using library default_collection_order: {self.library.default_collection_order}")
        self.custom_sort = self.playlist
        if test_sort:
            if self.smart:
                raise Failed(f"{self.Type} Error: collection_order does not work with Smart Collections")
            logger.debug("")
            logger.debug("Validating Method: collection_order")
            logger.debug(f"Value: {test_sort}")
            if test_sort.lower() in plex.collection_order_options:
                self.details["collection_order"] = test_sort.lower()
                if test_sort.lower() == "custom" and self.build_collection:
                    self.custom_sort = True
            elif (self.library.is_movie and test_sort.lower() in plex.movie_sorts) or (self.library.is_show and test_sort.lower() in plex.show_sorts):
                self.custom_sort = test_sort.lower()
            else:
                raise Failed(f"{self.Type} Error: {test_sort} collection_order invalid\n\trelease (Order Collection by release dates)\n\talpha (Order Collection Alphabetically)\n\tcustom (Custom Order Collection)\n\tOther sorting options can be found at https://github.com/meisnate12/Plex-Meta-Manager/wiki/Smart-Builders#sort-options")

        if self.smart_url or self.smart_label_collection:
            self.custom_sort = False

        for method_key, method_data in self.data.items():
            if method_key.lower() in ignored_details:
                continue
            logger.debug("")
            method_name, method_mod, method_final = self._split(method_key)
            if method_name in ignored_details:
                continue
            logger.debug(f"Validating Method: {method_key}")
            logger.debug(f"Value: {method_data}")
            try:
                if method_data is None and method_name in all_builders + plex.searches:
                    raise Failed(f"{self.Type} Error: {method_final} attribute is blank")
                elif method_data is None and method_final not in none_details:
                    logger.warning(f"Collection Warning: {method_final} attribute is blank")
                elif self.playlist and method_name not in playlist_attributes:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed when using playlists")
                elif not self.config.Trakt and "trakt" in method_name:
                    raise Failed(f"{self.Type} Error: {method_final} requires Trakt to be configured")
                elif not self.library.Radarr and "radarr" in method_name:
                    logger.error(f"{self.Type} Error: {method_final} requires Radarr to be configured")
                elif not self.library.Sonarr and "sonarr" in method_name:
                    logger.error(f"{self.Type} Error: {method_final} requires Sonarr to be configured")
                elif not self.library.Tautulli and "tautulli" in method_name:
                    raise Failed(f"{self.Type} Error: {method_final} requires Tautulli to be configured")
                elif not self.config.MyAnimeList and "mal" in method_name:
                    raise Failed(f"{self.Type} Error: {method_final} requires MyAnimeList to be configured")
                elif self.library.is_movie and method_name in show_only_builders:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for show libraries")
                elif self.library.is_show and method_name in movie_only_builders:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for movie libraries")
                elif self.library.is_show and method_name in plex.movie_only_searches:
                    raise Failed(f"{self.Type} Error: {method_final} plex search only allowed for movie libraries")
                elif self.library.is_movie and method_name in plex.show_only_searches:
                    raise Failed(f"{self.Type} Error: {method_final} plex search only allowed for show libraries")
                elif self.library.is_music and method_name not in music_attributes:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed for music libraries")
                elif self.library.is_music and method_name in album_details and self.collection_level != "album":
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for album collections")
                elif not self.library.is_music and method_name in music_only_builders:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for music libraries")
                elif not self.playlist and self.collection_level != "episode" and method_name in episode_parts_only:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed with Collection Level: episode")
                elif self.parts_collection and method_name not in parts_collection_valid:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed with Collection Level: {self.collection_level.capitalize()}")
                elif self.smart and method_name in smart_invalid:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed with normal collections")
                elif self.collectionless and method_name not in collectionless_details:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed for Collectionless collection")
                elif self.smart_url and method_name in all_builders + smart_url_invalid:
                    raise Failed(f"{self.Type} Error: {method_final} builder not allowed when using smart_filter")
                elif method_name in summary_details:
                    self._summary(method_name, method_data)
                elif method_name in poster_details:
                    self._poster(method_name, method_data)
                elif method_name in background_details:
                    self._background(method_name, method_data)
                elif method_name in details:
                    self._details(method_name, method_data, method_final, methods)
                elif method_name in item_details:
                    self._item_details(method_name, method_data, method_mod, method_final, methods)
                elif method_name in radarr_details:
                    self._radarr(method_name, method_data)
                elif method_name in sonarr_details:
                    self._sonarr(method_name, method_data)
                elif method_name in anidb.builders:
                    self._anidb(method_name, method_data)
                elif method_name in anilist.builders:
                    self._anilist(method_name, method_data)
                elif method_name in flixpatrol.builders:
                    self._flixpatrol(method_name, method_data)
                elif method_name in icheckmovies.builders:
                    self._icheckmovies(method_name, method_data)
                elif method_name in letterboxd.builders:
                    self._letterboxd(method_name, method_data)
                elif method_name in imdb.builders:
                    self._imdb(method_name, method_data)
                elif method_name in mal.builders:
                    self._mal(method_name, method_data)
                elif method_name in plex.builders or method_final in plex.searches:
                    self._plex(method_name, method_data)
                elif method_name in reciperr.builders:
                    self._reciperr(method_name, method_data)
                elif method_name in tautulli.builders:
                    self._tautulli(method_name, method_data)
                elif method_name in tmdb.builders:
                    self._tmdb(method_name, method_data)
                elif method_name in trakt.builders:
                    self._trakt(method_name, method_data)
                elif method_name in tvdb.builders:
                    self._tvdb(method_name, method_data)
                elif method_name in mdblist.builders:
                    self._mdblist(method_name, method_data)
                elif method_name == "filters":
                    self._filters(method_name, method_data)
                else:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not supported")
            except Failed as e:
                if self.validate_builders:
                    raise
                else:
                    logger.error(e)

        if not self.server_preroll and not self.smart_url and not self.blank_collection and len(self.builders) == 0:
            raise Failed(f"{self.Type} Error: No builders were found")

        if self.blank_collection and len(self.builders) > 0:
            raise Failed(f"{self.Type} Error: No builders allowed with blank_collection")

        if self.custom_sort is True and (len(self.builders) > 1 or self.builders[0][0] not in custom_sort_builders):
            raise Failed(f"{self.Type} Error: " + ('Playlists' if self.playlist else 'collection_order: custom') +
                         (f" can only be used with a single builder per {self.type}" if len(self.builders) > 1 else f" cannot be used with {self.builders[0][0]}"))

        if "add_missing" not in self.radarr_details:
            self.radarr_details["add_missing"] = self.library.Radarr.add_missing if self.library.Radarr else False
        if "add_existing" not in self.radarr_details:
            self.radarr_details["add_existing"] = self.library.Radarr.add_existing if self.library.Radarr else False

        if "add_missing" not in self.sonarr_details:
            self.sonarr_details["add_missing"] = self.library.Sonarr.add_missing if self.library.Sonarr else False
        if "add_existing" not in self.sonarr_details:
            self.sonarr_details["add_existing"] = self.library.Sonarr.add_existing if self.library.Sonarr else False
            
        if self.smart_url or self.collectionless or self.library.is_music:
            self.radarr_details["add_missing"] = False
            self.radarr_details["add_existing"] = False
            self.sonarr_details["add_missing"] = False
            self.sonarr_details["add_existing"] = False

        if (self.radarr_details["add_existing"] or self.sonarr_details["add_existing"]) and not self.parts_collection:
            self.item_details["add_existing"] = True

        if self.collectionless:
            self.details["collection_mode"] = "hide"
            self.sync = True

        self.do_missing = not self.no_missing and (self.details["show_missing"] or self.details["save_missing"]
                                                   or (self.library.Radarr and self.radarr_details["add_missing"])
                                                   or (self.library.Sonarr and self.sonarr_details["add_missing"]))

        if self.build_collection:
            try:
                self.obj = self.library.get_playlist(self.name) if self.playlist else self.library.get_collection(self.name)
                if (self.smart and not self.obj.smart) or (not self.smart and self.obj.smart):
                    logger.info("")
                    logger.error(f"{self.Type} Error: Converting {self.obj.title} to a {'smart' if self.smart else 'normal'} collection")
                    self.library.query(self.obj.delete)
                    self.obj = None
            except Failed:
                self.obj = None

            if self.obj:
                self.exists = True
                if not self.playlist:
                    self.beginning_count = self.obj.childCount
                if self.sync or self.playlist:
                    self.remove_item_map = {i.ratingKey: i for i in self.library.get_collection_items(self.obj, self.smart_label_collection)}
                    if self.playlist:
                        self.beginning_count = len(self.remove_item_map)
        else:
            self.obj = None
            self.sync = False
            self.run_again = False
        logger.info("")
        logger.info("Validation Successful")

    def _summary(self, method_name, method_data):
        if method_name == "summary":
            self.summaries[method_name] = method_data
        elif method_name == "tmdb_summary":
            self.summaries[method_name] = self.config.TMDb.get_movie_show_or_collection(util.regex_first_int(method_data, "TMDb ID"), self.library.is_movie).overview
        elif method_name == "tmdb_description":
            self.summaries[method_name] = self.config.TMDb.get_list(util.regex_first_int(method_data, "TMDb List ID")).description
        elif method_name == "tmdb_biography":
            self.summaries[method_name] = self.config.TMDb.get_person(util.regex_first_int(method_data, "TMDb Person ID")).biography
        elif method_name == "tvdb_summary":
            self.summaries[method_name] = self.config.TVDb.get_item(method_data, self.library.is_movie).summary
        elif method_name == "tvdb_description":
            self.summaries[method_name] = self.config.TVDb.get_list_description(method_data)
        elif method_name == "trakt_description":
            self.summaries[method_name] = self.config.Trakt.list_description(self.config.Trakt.validate_list(method_data, self.library.is_movie)[0])
        elif method_name == "letterboxd_description":
            self.summaries[method_name] = self.config.Letterboxd.get_list_description(method_data, self.language)
        elif method_name == "icheckmovies_description":
            self.summaries[method_name] = self.config.ICheckMovies.get_list_description(method_data, self.language)

    def _poster(self, method_name, method_data):
        if method_name == "url_poster":
            self.posters[method_name] = method_data
        elif method_name == "tmdb_poster":
            self.posters[method_name] = self.config.TMDb.get_movie_show_or_collection(util.regex_first_int(method_data, 'TMDb ID'), self.library.is_movie).poster_url
        elif method_name == "tmdb_profile":
            self.posters[method_name] = self.config.TMDb.get_person(util.regex_first_int(method_data, 'TMDb Person ID')).profile_url
        elif method_name == "tvdb_poster":
            self.posters[method_name] = f"{self.config.TVDb.get_item(method_data, self.library.is_movie).poster_path}"
        elif method_name == "file_poster":
            if os.path.exists(os.path.abspath(method_data)):
                self.posters[method_name] = os.path.abspath(method_data)
            else:
                logger.error(f"{self.Type} Error: Poster Path Does Not Exist: {os.path.abspath(method_data)}")

    def _background(self, method_name, method_data):
        if method_name == "url_background":
            self.backgrounds[method_name] = method_data
        elif method_name == "tmdb_background":
            self.backgrounds[method_name] = self.config.TMDb.get_movie_show_or_collection(util.regex_first_int(method_data, 'TMDb ID'), self.library.is_movie).backdrop_url
        elif method_name == "tvdb_background":
            self.posters[method_name] = f"{self.config.TVDb.get_item(method_data, self.library.is_movie).background_path}"
        elif method_name == "file_background":
            if os.path.exists(os.path.abspath(method_data)):
                self.backgrounds[method_name] = os.path.abspath(method_data)
            else:
                logger.error(f"{self.Type} Error: Background Path Does Not Exist: {os.path.abspath(method_data)}")

    def _details(self, method_name, method_data, method_final, methods):
        if method_name == "url_theme":
            self.url_theme = method_data
        elif method_name == "file_theme":
            if os.path.exists(os.path.abspath(method_data)):
                self.file_theme = os.path.abspath(method_data)
            else:
                logger.error(f"{self.Type} Error: Theme Path Does Not Exist: {os.path.abspath(method_data)}")
        elif method_name == "tmdb_region":
            self.tmdb_region = util.parse(self.Type, method_name, method_data, options=self.config.TMDb.iso_3166_1)
        elif method_name == "collection_mode":
            self.details[method_name] = util.check_collection_mode(method_data)
        elif method_name == "minimum_items":
            self.minimum = util.parse(self.Type, method_name, method_data, datatype="int", minimum=1)
        elif method_name == "limit":
            self.limit = util.parse(self.Type, method_name, method_data, datatype="int", minimum=1)
        elif method_name == "cache_builders":
            self.details[method_name] = util.parse(self.Type, method_name, method_data, datatype="int", minimum=0)
        elif method_name == "server_preroll":
            self.server_preroll = util.parse(self.Type, method_name, method_data)
        elif method_name == "ignore_ids":
            self.ignore_ids.extend(util.parse(self.Type, method_name, method_data, datatype="intlist"))
        elif method_name == "ignore_imdb_ids":
            self.ignore_imdb_ids.extend(util.parse(self.Type, method_name, method_data, datatype="list"))
        elif method_name == "label":
            if "label" in methods and "label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use label and label.sync together")
            if "label.remove" in methods and "label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use label.remove and label.sync together")
            if method_final == "label" and "label_sync_mode" in methods and self.data[methods["label_sync_mode"]] == "sync":
                self.details["label.sync"] = util.get_list(method_data) if method_data else []
            else:
                self.details[method_final] = util.get_list(method_data) if method_data else []
        elif method_name == "changes_webhooks":
            self.details[method_name] = util.parse(self.Type, method_name, method_data, datatype="list")
        elif method_name in scheduled_boolean:
            if isinstance(method_data, bool):
                self.details[method_name] = method_data
            elif isinstance(method_data, (int, float)):
                self.details[method_name] = method_data > 0
            elif str(method_data).lower() in ["t", "true"]:
                self.details[method_name] = True
            elif str(method_data).lower() in ["f", "false"]:
                self.details[method_name] = False
            else:
                try:
                    util.schedule_check(method_name, util.parse(self.Type, method_name, method_data), self.current_time, self.config.run_hour)
                    self.details[method_name] = True
                except NotScheduled:
                    self.details[method_name] = False
        elif method_name in boolean_details:
            default = self.details[method_name] if method_name in self.details else None
            self.details[method_name] = util.parse(self.Type, method_name, method_data, datatype="bool", default=default)
        elif method_name in string_details:
            self.details[method_name] = str(method_data)

    def _item_details(self, method_name, method_data, method_mod, method_final, methods):
        if method_name == "item_label":
            if "item_label" in methods and "item_label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use item_label and item_label.sync together")
            if "item_label.remove" in methods and "item_label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use item_label.remove and item_label.sync together")
            self.item_details[method_final] = util.get_list(method_data) if method_data else []
        elif method_name == "non_item_remove_label":
            if not method_data:
                raise Failed(f"{self.Type} Error: non_item_remove_label is blank")
            self.item_details[method_final] = util.get_list(method_data)
        elif method_name in ["item_radarr_tag", "item_sonarr_tag"]:
            if method_name in methods and f"{method_name}.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use {method_name} and {method_name}.sync together")
            if f"{method_name}.remove" in methods and f"{method_name}.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use {method_name}.remove and {method_name}.sync together")
            if method_name in methods and f"{method_name}.remove" in methods:
                raise Failed(f"{self.Type} Error: Cannot use {method_name} and {method_name}.remove together")
            self.item_details[method_name] = util.get_list(method_data, lower=True)
            self.item_details["apply_tags"] = method_mod[1:] if method_mod else ""
        elif method_name == "item_overlay":
            if isinstance(method_data, dict):
                if "name" not in method_data or not method_data["name"]:
                    raise Failed(f"{self.Type} Error: item_overlay must have the name attribute")
                if "git" in method_data and method_data["git"]:
                    url = f"https://github.com/meisnate12/Plex-Meta-Manager-Configs/blob/master/{method_data['git']}.png"
                elif "url" in method_data and method_data["url"]:
                    url = method_data["url"]
                else:
                    raise Failed(f"{self.Type} Error: item_overlay must have either the git or url attribute")
                name = method_data["name"]
                response = self.config.get(url)
                if response.status_code >= 400:
                    raise Failed(f"{self.Type} Error: Overlay Image not found at: {url}")
                overlay_dir = os.path.join(self.config.default_dir, "overlays", name)
                if not os.path.exists(overlay_dir) or not os.path.isdir(overlay_dir):
                    os.makedirs(overlay_dir, exist_ok=False)
                    logger.info(f"Creating Overlay Folder found at: {overlay_dir}")
                overlay = os.path.join(overlay_dir, "overlay.png")
                with open(overlay, "wb") as handler:
                    handler.write(response.content)
                while util.is_locked(overlay):
                    time.sleep(1)
            else:
                overlay = os.path.join(self.config.default_dir, "overlays", method_data, "overlay.png")
                name = method_data
            if not os.path.exists(overlay):
                raise Failed(f"{self.Type} Error: {name} overlay image not found at {overlay}")
            if name in self.library.overlays:
                raise Failed("Each Overlay can only be used once per Library")
            self.library.overlays.append(name)
            self.item_details[method_name] = name
        elif method_name == "item_refresh_delay":
            self.item_details[method_name] = util.parse(self.Type, method_name, method_data, datatype="int", default=0, minimum=0)
        elif method_name in item_bool_details:
            if util.parse(self.Type, method_name, method_data, datatype="bool", default=False):
                self.item_details[method_name] = True
            elif method_name in item_false_details:
                self.item_details[method_name] = False
        elif method_name in plex.item_advance_keys:
            key, options = plex.item_advance_keys[method_name]
            if method_name in advance_new_agent and self.library.agent not in plex.new_plex_agents:
                logger.error(f"Metadata Error: {method_name} attribute only works for with the New Plex Movie Agent and New Plex TV Agent")
            elif method_name in advance_show and not self.library.is_show:
                logger.error(f"Metadata Error: {method_name} attribute only works for show libraries")
            elif str(method_data).lower() not in options:
                logger.error(f"Metadata Error: {method_data} {method_name} attribute invalid")
            else:
                self.item_details[method_name] = str(method_data).lower()

    def _radarr(self, method_name, method_data):
        if method_name in ["radarr_add_missing", "radarr_add_existing", "radarr_monitor", "radarr_search"]:
            self.radarr_details[method_name[7:]] = util.parse(self.Type, method_name, method_data, datatype="bool")
        elif method_name == "radarr_folder":
            self.radarr_details["folder"] = method_data
        elif method_name == "radarr_availability":
            if str(method_data).lower() in radarr.availability_translation:
                self.radarr_details["availability"] = str(method_data).lower()
            else:
                raise Failed(f"{self.Type} Error: {method_name} attribute must be either announced, cinemas, released or db")
        elif method_name == "radarr_quality":
            self.radarr_details["quality"] = method_data
        elif method_name == "radarr_tag":
            self.radarr_details["tag"] = util.get_list(method_data, lower=True)

    def _sonarr(self, method_name, method_data):
        if method_name in ["sonarr_add_missing", "sonarr_add_existing", "sonarr_season", "sonarr_search", "sonarr_cutoff_search"]:
            self.sonarr_details[method_name[7:]] = util.parse(self.Type, method_name, method_data, datatype="bool")
        elif method_name in ["sonarr_folder", "sonarr_quality", "sonarr_language"]:
            self.sonarr_details[method_name[7:]] = method_data
        elif method_name == "sonarr_monitor":
            if str(method_data).lower() in sonarr.monitor_translation:
                self.sonarr_details["monitor"] = str(method_data).lower()
            else:
                raise Failed(f"{self.Type} Error: {method_name} attribute must be either all, future, missing, existing, pilot, first, latest or none")
        elif method_name == "sonarr_series":
            if str(method_data).lower() in sonarr.series_types:
                self.sonarr_details["series"] = str(method_data).lower()
            else:
                raise Failed(f"{self.Type} Error: {method_name} attribute must be either standard, daily, or anime")
        elif method_name == "sonarr_tag":
            self.sonarr_details["tag"] = util.get_list(method_data, lower=True)

    def _anidb(self, method_name, method_data):
        if method_name == "anidb_popular":
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=30, maximum=30)))
        elif method_name in ["anidb_id", "anidb_relation"]:
            for anidb_id in self.config.AniDB.validate_anidb_ids(method_data):
                self.builders.append((method_name, anidb_id))
        elif method_name == "anidb_tag":
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {}
                if "tag" not in dict_methods:
                    raise Failed(f"{self.Type} Error: anidb_tag tag attribute is required")
                elif not dict_data[dict_methods["tag"]]:
                    raise Failed(f"{self.Type} Error: anidb_tag tag attribute is blank")
                else:
                    new_dictionary["tag"] = util.regex_first_int(dict_data[dict_methods["tag"]], "AniDB Tag ID")
                new_dictionary["limit"] = util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name, minimum=0)
                self.builders.append((method_name, new_dictionary))

    def _anilist(self, method_name, method_data):
        if method_name in ["anilist_id", "anilist_relations", "anilist_studio"]:
            for anilist_id in self.config.AniList.validate_anilist_ids(method_data, studio=method_name == "anilist_studio"):
                self.builders.append((method_name, anilist_id))
        elif method_name in ["anilist_popular", "anilist_trending", "anilist_top_rated"]:
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10)))
        elif method_name == "anilist_userlist":
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                self.builders.append((method_name, self.config.AniList.validate_userlist({
                    "username": util.parse(self.Type, "username", dict_data, methods=dict_methods, parent=method_name),
                    "list_name": util.parse(self.Type, "list_name", dict_data, methods=dict_methods, parent=method_name),
                    "sort_by": util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="score", options=anilist.userlist_sort_options),
                })))
        elif method_name == "anilist_search":
            if self.current_time.month in [12, 1, 2]:           current_season = "winter"
            elif self.current_time.month in [3, 4, 5]:          current_season = "spring"
            elif self.current_time.month in [6, 7, 8]:          current_season = "summer"
            else:                                               current_season = "fall"
            default_year = self.current_year + 1 if self.current_time.month == 12 else self.current_year
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {}
                for search_method, search_data in dict_data.items():
                    search_attr, modifier = os.path.splitext(str(search_method).lower())
                    if search_method not in anilist.searches:
                        raise Failed(f"{self.Type} Error: {method_name} {search_method} attribute not supported")
                    elif search_attr == "season":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, parent=method_name, default=current_season, options=util.seasons)
                        if new_dictionary[search_attr] == "current":
                            new_dictionary[search_attr] = current_season
                        if "year" not in dict_methods:
                            logger.warning(f"Collection Warning: {method_name} year attribute not found using this year: {default_year} by default")
                            new_dictionary["year"] = default_year
                    elif search_attr == "year":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, datatype="int", parent=method_name, default=default_year, minimum=1917, maximum=default_year + 1)
                    elif search_data is None:
                        raise Failed(f"{self.Type} Error: {method_name} {search_method} attribute is blank")
                    elif search_attr == "adult":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, datatype="bool", parent=method_name)
                    elif search_attr == "country":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, options=anilist.country_codes, parent=method_name)
                    elif search_attr == "source":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, options=anilist.media_source, parent=method_name)
                    elif search_attr in ["episodes", "duration", "score", "popularity"]:
                        new_dictionary[search_method] = util.parse(self.Type, search_method, search_data, datatype="int", parent=method_name)
                    elif search_attr in ["format", "status", "genre", "tag", "tag_category"]:
                        new_dictionary[search_method] = self.config.AniList.validate(search_attr.replace("_", " ").title(), util.parse(self.Type, search_method, search_data))
                    elif search_attr in ["start", "end"]:
                        new_dictionary[search_method] = util.validate_date(search_data, f"{method_name} {search_method} attribute", return_as="%m/%d/%Y")
                    elif search_attr == "min_tag_percent":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, datatype="int", parent=method_name, minimum=0, maximum=100)
                    elif search_attr == "search":
                        new_dictionary[search_attr] = str(search_data)
                    elif search_method not in ["sort_by", "limit"]:
                        raise Failed(f"{self.Type} Error: {method_name} {search_method} attribute not supported")
                if len(new_dictionary) == 0:
                    raise Failed(f"{self.Type} Error: {method_name} must have at least one valid search option")
                new_dictionary["sort_by"] = util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="score", options=anilist.sort_options)
                new_dictionary["limit"] = util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name)
                self.builders.append((method_name, new_dictionary))

    def _flixpatrol(self, method_name, method_data):
        if method_name.startswith("flixpatrol_url"):
            flixpatrol_lists = self.config.FlixPatrol.validate_flixpatrol_lists(method_data, self.language, self.library.is_movie)
            for flixpatrol_list in flixpatrol_lists:
                self.builders.append(("flixpatrol_url", flixpatrol_list))
        elif method_name in flixpatrol.builders:
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                if method_name == "flixpatrol_demographics":
                    data = {
                        "generation": util.parse(self.Type, "generation", dict_data, methods=dict_methods, parent=method_name, options=flixpatrol.generations),
                        "gender": util.parse(self.Type, "gender", dict_data, methods=dict_methods, parent=method_name, default="all", options=flixpatrol.gender),
                        "location": util.parse(self.Type, "location", dict_data, methods=dict_methods, parent=method_name, default="world", options=flixpatrol.demo_locations),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, parent=method_name, default=10)
                    }
                elif method_name == "flixpatrol_popular":
                    data = {
                        "source": util.parse(self.Type, "source", dict_data, methods=dict_methods, parent=method_name, options=flixpatrol.popular),
                        "time_window": util.parse(self.Type, "time_window", dict_data, methods=dict_methods, parent=method_name, default="today"),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, parent=method_name, default=10)
                    }
                elif method_name == "flixpatrol_top":
                    data = {
                        "platform": util.parse(self.Type, "platform", dict_data, methods=dict_methods, parent=method_name, options=flixpatrol.platforms),
                        "location": util.parse(self.Type, "location", dict_data, methods=dict_methods, parent=method_name, default="world", options=flixpatrol.locations),
                        "time_window": util.parse(self.Type, "time_window", dict_data, methods=dict_methods, parent=method_name, default="today"),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, parent=method_name, default=10)
                    }
                else:
                    continue
                if self.config.FlixPatrol.validate_flixpatrol_dict(method_name, data, self.language, self.library.is_movie):
                    self.builders.append((method_name, data))

    def _icheckmovies(self, method_name, method_data):
        if method_name.startswith("icheckmovies_list"):
            icheckmovies_lists = self.config.ICheckMovies.validate_icheckmovies_lists(method_data, self.language)
            for icheckmovies_list in icheckmovies_lists:
                self.builders.append(("icheckmovies_list", icheckmovies_list))
            if method_name.endswith("_details"):
                self.summaries[method_name] = self.config.ICheckMovies.get_list_description(icheckmovies_lists[0], self.language)

    def _imdb(self, method_name, method_data):
        if method_name == "imdb_id":
            for value in util.get_list(method_data):
                if str(value).startswith("tt"):
                    self.builders.append((method_name, value))
                else:
                    raise Failed(f"{self.Type} Error: imdb_id {value} must begin with tt")
        elif method_name == "imdb_list":
            for imdb_dict in self.config.IMDb.validate_imdb_lists(self.Type, method_data, self.language):
                self.builders.append((method_name, imdb_dict))
        elif method_name == "imdb_chart":
            for value in util.get_list(method_data):
                if value in imdb.movie_charts and not self.library.is_movie:
                    raise Failed(f"{self.Type} Error: chart: {value} does not work with show libraries")
                elif value in imdb.show_charts and self.library.is_movie:
                    raise Failed(f"{self.Type} Error: chart: {value} does not work with movie libraries")
                elif value in imdb.charts:
                    self.builders.append((method_name, value))
                else:
                    raise Failed(f"{self.Type} Error: chart: {value} is invalid options are {[i for i in imdb.charts]}")

    def _letterboxd(self, method_name, method_data):
        if method_name.startswith("letterboxd_list"):
            letterboxd_lists = self.config.Letterboxd.validate_letterboxd_lists(self.Type, method_data, self.language)
            for letterboxd_list in letterboxd_lists:
                self.builders.append(("letterboxd_list", letterboxd_list))
            if method_name.endswith("_details"):
                self.summaries[method_name] = self.config.Letterboxd.get_list_description(letterboxd_lists[0]["url"], self.language)

    def _mal(self, method_name, method_data):
        if method_name == "mal_id":
            for mal_id in util.get_int_list(method_data, "MyAnimeList ID"):
                self.builders.append((method_name, mal_id))
        elif method_name in ["mal_all", "mal_airing", "mal_upcoming", "mal_tv", "mal_ova", "mal_movie", "mal_special", "mal_popular", "mal_favorite", "mal_suggested"]:
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10, maximum=100 if method_name == "mal_suggested" else 500)))
        elif method_name in ["mal_season", "mal_userlist"]:
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                if method_name == "mal_season":
                    if self.current_time.month in [1, 2, 3]:            default_season = "winter"
                    elif self.current_time.month in [4, 5, 6]:          default_season = "spring"
                    elif self.current_time.month in [7, 8, 9]:          default_season = "summer"
                    else:                                               default_season = "fall"
                    season = util.parse(self.Type, "season", dict_data, methods=dict_methods, parent=method_name, default=default_season, options=util.seasons)
                    if season == "current":
                        season = default_season
                    self.builders.append((method_name, {
                        "season": season,
                        "sort_by": util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="members", options=mal.season_sort_options, translation=mal.season_sort_translation),
                        "year": util.parse(self.Type, "year", dict_data, datatype="int", methods=dict_methods, default=self.current_year, parent=method_name, minimum=1917, maximum=self.current_year + 1),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=100, parent=method_name, maximum=500)
                    }))
                elif method_name == "mal_userlist":
                    self.builders.append((method_name, {
                        "username": util.parse(self.Type, "username", dict_data, methods=dict_methods, parent=method_name),
                        "status": util.parse(self.Type, "status", dict_data, methods=dict_methods, parent=method_name, default="all", options=mal.userlist_status),
                        "sort_by": util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="score", options=mal.userlist_sort_options, translation=mal.userlist_sort_translation),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=100, parent=method_name, maximum=1000)
                    }))
        elif method_name in ["mal_genre", "mal_studio"]:
            id_name = f"{method_name[4:]}_id"
            final_data = []
            for data in util.get_list(method_data):
                final_data.append(data if isinstance(data, dict) else {id_name: data, "limit": 0})
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                self.builders.append((method_name, {
                    id_name: util.parse(self.Type, id_name, dict_data, datatype="int", methods=dict_methods, parent=method_name, maximum=999999),
                    "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name)
                }))

    def _plex(self, method_name, method_data):
        if method_name in ["plex_all", "plex_pilots"]:
            self.builders.append((method_name, self.collection_level))
        elif method_name in ["plex_search", "plex_collectionless"]:
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {}
                if method_name == "plex_search":
                    type_override = f"{self.collection_level}s" if self.collection_level in plex.collection_level_options else None
                    new_dictionary = self.build_filter("plex_search", dict_data, type_override=type_override)
                elif method_name == "plex_collectionless":
                    prefix_list = util.parse(self.Type, "exclude_prefix", dict_data, datatype="list", methods=dict_methods) if "exclude_prefix" in dict_methods else []
                    exact_list = util.parse(self.Type, "exclude", dict_data, datatype="list", methods=dict_methods) if "exclude" in dict_methods else []
                    if len(prefix_list) == 0 and len(exact_list) == 0:
                        raise Failed(f"{self.Type} Error: you must have at least one exclusion")
                    exact_list.append(self.name)
                    new_dictionary["exclude_prefix"] = prefix_list
                    new_dictionary["exclude"] = exact_list
                self.builders.append((method_name, new_dictionary))
        else:
            self.builders.append(("plex_search", self.build_filter("plex_search", {"any": {method_name: method_data}})))

    def _reciperr(self, method_name, method_data):
        if method_name == "reciperr_list":
            for reciperr_list in self.config.Reciperr.validate_list(method_data):
                self.builders.append((method_name, reciperr_list))
        elif method_name == "stevenlu_popular":
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, "bool")))

    def _mdblist(self, method_name, method_data):
        for mdb_dict in self.config.Mdblist.validate_mdblist_lists(self.Type, method_data):
            self.builders.append((method_name, mdb_dict))

    def _tautulli(self, method_name, method_data):
        for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
            dict_methods = {dm.lower(): dm for dm in dict_data}
            self.builders.append((method_name, {
                "list_type": "popular" if method_name == "tautulli_popular" else "watched",
                "list_days": util.parse(self.Type, "list_days", dict_data, datatype="int", methods=dict_methods, default=30, parent=method_name),
                "list_size": util.parse(self.Type, "list_size", dict_data, datatype="int", methods=dict_methods, default=10, parent=method_name),
                "list_buffer": util.parse(self.Type, "list_buffer", dict_data, datatype="int", methods=dict_methods, default=20, parent=method_name),
                "list_minimum": util.parse(self.Type, "list_minimum", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name)
            }))

    def _tmdb(self, method_name, method_data):
        if method_name == "tmdb_discover":
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {"limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=100, parent=method_name)}
                for discover_method, discover_data in dict_data.items():
                    discover_attr, modifier = os.path.splitext(str(discover_method).lower())
                    if discover_data is None:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute is blank")
                    elif discover_method not in tmdb.discover_all:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute not supported")
                    elif self.library.is_movie and discover_attr in tmdb.discover_tv_only:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute only works for show libraries")
                    elif self.library.is_show and discover_attr in tmdb.discover_movie_only:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute only works for movie libraries")
                    elif discover_attr == "region":
                        new_dictionary[discover_attr] = util.parse(self.Type, discover_attr, discover_data, parent=method_name, regex=("^[A-Z]{2}$", "US"))
                    elif discover_attr == "sort_by":
                        options = tmdb.discover_movie_sort if self.library.is_movie else tmdb.discover_tv_sort
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, parent=method_name, options=options)
                    elif discover_attr == "certification_country":
                        if "certification" in dict_data or "certification.lte" in dict_data or "certification.gte" in dict_data:
                            new_dictionary[discover_method] = discover_data
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_attr} attribute: must be used with either certification, certification.lte, or certification.gte")
                    elif discover_attr == "certification":
                        if "certification_country" in dict_data:
                            new_dictionary[discover_method] = discover_data
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute: must be used with certification_country")
                    elif discover_attr == "watch_region":
                        if "with_watch_providers" in dict_data or "without_watch_providers" in dict_data or "with_watch_monetization_types" in dict_data:
                            new_dictionary[discover_method] = discover_data
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute: must be used with either with_watch_providers, without_watch_providers, or with_watch_monetization_types")
                    elif discover_attr == "with_watch_monetization_types":
                        if "watch_region" in dict_data:
                            new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, parent=method_name, options=tmdb.discover_monetization_types)
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute: must be used with watch_region")
                    elif discover_attr in tmdb.discover_booleans:
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="bool", parent=method_name)
                    elif discover_attr == "vote_average":
                        new_dictionary[discover_method] = util.parse(self.Type, discover_method, discover_data, datatype="float", parent=method_name)
                    elif discover_attr == "with_status":
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="int", parent=method_name, minimum=0, maximum=5)
                    elif discover_attr == "with_type":
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="int", parent=method_name, minimum=0, maximum=6)
                    elif discover_attr in tmdb.discover_dates:
                        new_dictionary[discover_method] = util.validate_date(discover_data, f"{method_name} {discover_method} attribute", return_as="%m/%d/%Y")
                    elif discover_attr in tmdb.discover_years:
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="int", parent=method_name, minimum=1800, maximum=self.current_year + 1)
                    elif discover_attr in tmdb.discover_ints:
                        new_dictionary[discover_method] = util.parse(self.Type, discover_method, discover_data, datatype="int", parent=method_name)
                    elif discover_attr in tmdb.discover_strings:
                        new_dictionary[discover_method] = discover_data
                    elif discover_attr != "limit":
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute not supported")
                if len(new_dictionary) > 1:
                    self.builders.append((method_name, new_dictionary))
                else:
                    raise Failed(f"{self.Type} Error: {method_name} had no valid fields")
        elif method_name in tmdb.int_builders:
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10)))
        else:
            values = self.config.TMDb.validate_tmdb_ids(method_data, method_name)
            if method_name in tmdb.details_builders:
                if method_name.startswith(("tmdb_collection", "tmdb_movie", "tmdb_show")):
                    item = self.config.TMDb.get_movie_show_or_collection(values[0], self.library.is_movie)
                    if item.overview:
                        self.summaries[method_name] = item.overview
                    if item.backdrop_url:
                        self.backgrounds[method_name] = item.backdrop_url
                    if item.poster_path:
                        self.posters[method_name] = item.poster_url
                elif method_name.startswith(("tmdb_actor", "tmdb_crew", "tmdb_director", "tmdb_producer", "tmdb_writer")):
                    item = self.config.TMDb.get_person(values[0])
                    if item.biography:
                        self.summaries[method_name] = item.biography
                    if item.profile_path:
                        self.posters[method_name] = item.profile_url
                elif method_name.startswith("tmdb_list"):
                    item = self.config.TMDb.get_list(values[0])
                    if item.description:
                        self.summaries[method_name] = item.description
            for value in values:
                self.builders.append((method_name[:-8] if method_name in tmdb.details_builders else method_name, value))

    def _trakt(self, method_name, method_data):
        if method_name.startswith("trakt_list"):
            trakt_lists = self.config.Trakt.validate_list(method_data)
            for trakt_list in trakt_lists:
                self.builders.append(("trakt_list", trakt_list))
            if method_name.endswith("_details"):
                self.summaries[method_name] = self.config.Trakt.list_description(trakt_lists[0])
        elif method_name == "trakt_boxoffice":
            if util.parse(self.Type, method_name, method_data, datatype="bool", default=False):
                self.builders.append((method_name, 10))
            else:
                raise Failed(f"{self.Type} Error: {method_name} must be set to true")
        elif method_name == "trakt_recommendations":
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10, maximum=100)))
        elif method_name in trakt.builders:
            if method_name in ["trakt_chart", "trakt_userlist"]:
                trakt_dicts = method_data
                final_method = method_name
            elif method_name in ["trakt_watchlist", "trakt_collection"]:
                trakt_dicts = []
                for trakt_user in util.get_list(method_data, split=False):
                    trakt_dicts.append({"userlist": "watchlist" if "trakt_watchlist" else "collected", "user": trakt_user})
                final_method = "trakt_userlist"
            else:
                terms = method_name.split("_")
                trakt_dicts = {
                    "chart": terms[1],
                    "amount": util.parse(self.Type, method_name, method_data, datatype="int", default=10),
                    "time_period": terms[2] if len(terms) > 2 else None
                }
                final_method = "trakt_chart"
            if method_name != final_method:
                logger.warning(f"{self.Type} Warning: {method_name} will run as {final_method}")
            for trakt_dict in self.config.Trakt.validate_chart(self.Type, final_method, trakt_dicts,  self.library.is_movie):
                self.builders.append((final_method, trakt_dict))

    def _tvdb(self, method_name, method_data):
        values = util.get_list(method_data)
        if method_name.endswith("_details"):
            if method_name.startswith(("tvdb_movie", "tvdb_show")):
                item = self.config.TVDb.get_item(values[0], method_name.startswith("tvdb_movie"))
                if item.background_path:
                    self.backgrounds[method_name] = item.background_path
                if item.poster_path:
                    self.posters[method_name] = item.poster_path
            elif method_name.startswith("tvdb_list"):
                self.summaries[method_name] = self.config.TVDb.get_list_description(values[0])
        for value in values:
            self.builders.append((method_name[:-8] if method_name.endswith("_details") else method_name, value))

    def _filters(self, method_name, method_data):
        dict_data = util.parse(self.Type, method_name, method_data, datatype="dict")
        dict_methods = {dm.lower(): dm for dm in dict_data}
        validate = True
        if "validate" in dict_methods:
            if dict_data[dict_methods["validate"]] is None:
                raise Failed(f"{self.Type} Error: validate filter attribute is blank")
            if not isinstance(dict_data[dict_methods["validate"]], bool):
                raise Failed(f"{self.Type} Error: validate filter attribute must be either true or false")
            validate = dict_data.pop(dict_methods["validate"])
        for filter_method, filter_data in dict_data.items():
            filter_attr, modifier, filter_final = self._split(filter_method)
            message = None
            if filter_final not in all_filters:
                message = f"{self.Type} Error: {filter_final} is not a valid filter attribute"
            elif self.collection_level in filters and filter_attr not in filters[self.collection_level]:
                message = f"{self.Type} Error: {filter_final} is not a valid {self.collection_level} filter attribute"
            elif filter_final is None:
                message = f"{self.Type} Error: {filter_final} filter attribute is blank"
            elif filter_attr in tmdb_filters:
                self.tmdb_filters.append((filter_final, self.validate_attribute(filter_attr, modifier, f"{filter_final} filter", filter_data, validate)))
            else:
                self.filters.append((filter_final, self.validate_attribute(filter_attr, modifier, f"{filter_final} filter", filter_data, validate)))
            if message:
                if validate:
                    raise Failed(message)
                else:
                    logger.error(message)

    def gather_ids(self, method, value):
        expired = None
        list_key = None
        if self.config.Cache and self.details["cache_builders"]:
            list_key, expired = self.config.Cache.query_list_cache(method, str(value), self.details["cache_builders"])
            if list_key and expired is False:
                logger.info(f"Builder: {method} loaded from Cache")
                return self.config.Cache.query_list_ids(list_key)
        if "plex" in method:
            ids = self.library.get_rating_keys(method, value)
        elif "tautulli" in method:
            ids = self.library.Tautulli.get_rating_keys(self.library, value, self.playlist)
        elif "anidb" in method:
            anidb_ids = self.config.AniDB.get_anidb_ids(method, value)
            ids = self.config.Convert.anidb_to_ids(anidb_ids, self.library)
        elif "anilist" in method:
            anilist_ids = self.config.AniList.get_anilist_ids(method, value)
            ids = self.config.Convert.anilist_to_ids(anilist_ids, self.library)
        elif "mal" in method:
            mal_ids = self.config.MyAnimeList.get_mal_ids(method, value)
            ids = self.config.Convert.myanimelist_to_ids(mal_ids, self.library)
        elif "tvdb" in method:
            ids = self.config.TVDb.get_tvdb_ids(method, value)
        elif "imdb" in method:
            ids = self.config.IMDb.get_imdb_ids(method, value, self.language)
        elif "flixpatrol" in method:
            ids = self.config.FlixPatrol.get_tmdb_ids(method, value, self.language, self.library.is_movie)
        elif "icheckmovies" in method:
            ids = self.config.ICheckMovies.get_imdb_ids(method, value, self.language)
        elif "letterboxd" in method:
            ids = self.config.Letterboxd.get_tmdb_ids(method, value, self.language)
        elif "reciperr" in method or "stevenlu" in method:
            ids = self.config.Reciperr.get_imdb_ids(method, value)
        elif "mdblist" in method:
            ids = self.config.Mdblist.get_imdb_ids(method, value)
        elif "tmdb" in method:
            ids = self.config.TMDb.get_tmdb_ids(method, value, self.library.is_movie, self.tmdb_region)
        elif "trakt" in method:
            ids = self.config.Trakt.get_trakt_ids(method, value, self.library.is_movie)
        else:
            ids = []
            logger.error(f"{self.Type} Error: {method} method not supported")
        if self.config.Cache and self.details["cache_builders"] and ids:
            if list_key:
                self.config.Cache.delete_list_ids(list_key)
            list_key = self.config.Cache.update_list_cache(method, str(value), expired, self.details["cache_builders"])
            self.config.Cache.update_list_ids(list_key, ids)
        return ids

    def filter_and_save_items(self, ids):
        items = []
        if len(ids) > 0:
            total_ids = len(ids)
            logger.debug("")
            logger.debug(f"{total_ids} IDs Found: {ids}")
            logger.debug("")
            for i, input_data in enumerate(ids, 1):
                input_id, id_type = input_data
                logger.ghost(f"Parsing ID {i}/{total_ids}")
                rating_keys = []
                if id_type == "ratingKey":
                    rating_keys = int(input_id)
                elif id_type == "imdb":
                    if input_id not in self.ignore_imdb_ids:
                        found = False
                        for pl_library in self.libraries:
                            if input_id in pl_library.imdb_map:
                                found = True
                                rating_keys = pl_library.imdb_map[input_id]
                                break
                        if not found and (self.collection_level == "episode" or self.playlist or self.do_missing):
                            try:
                                _id, tmdb_type = self.config.Convert.imdb_to_tmdb(input_id, fail=True)
                                if tmdb_type == "episode" and (self.collection_level == "episode" or self.playlist):
                                    try:
                                        tmdb_id, season_num, episode_num = _id.split("_")
                                        tvdb_id = self.config.Convert.tmdb_to_tvdb(tmdb_id, fail=True)
                                        tvdb_id = int(tvdb_id)
                                    except Failed as e:
                                        try:
                                            if not self.config.OMDb:
                                                raise Failed("")
                                            if self.config.OMDb.limit:
                                                raise Failed(" and OMDb limit reached.")
                                            omdb_item = self.config.OMDb.get_omdb(input_id)
                                            tvdb_id = omdb_item.series_id
                                            season_num = omdb_item.season_num
                                            episode_num = omdb_item.episode_num
                                            if not tvdb_id or not season_num or not episode_num:
                                                raise Failed(f" and OMDb metadata lookup Failed for IMDb ID: {input_id}")
                                        except Failed as ee:
                                            logger.error(f"{e}{ee}")
                                            continue
                                    for pl_library in self.libraries:
                                        if tvdb_id in pl_library.show_map:
                                            found = True
                                            show_item = pl_library.fetchItem(pl_library.show_map[tvdb_id][0])
                                            try:
                                                items.append(show_item.episode(season=int(season_num), episode=int(episode_num)))
                                            except NotFound:
                                                self.missing_parts.append(f"{show_item.title} Season: {season_num} Episode: {episode_num} Missing")
                                            break
                                    if not found and tvdb_id not in self.missing_shows and self.do_missing:
                                        self.missing_shows.append(tvdb_id)
                                elif tmdb_type == "movie" and self.do_missing and _id not in self.missing_movies:
                                    self.missing_movies.append(_id)
                                elif tmdb_type == "show" and self.do_missing:
                                    tvdb_id = self.config.Convert.tmdb_to_tvdb(_id, fail=True)
                                    if tvdb_id not in self.missing_shows:
                                        self.missing_shows.append(tvdb_id)
                            except Failed as e:
                                logger.warning(e)
                                continue
                elif id_type == "tmdb" and not self.parts_collection:
                    input_id = int(input_id)
                    if input_id not in self.ignore_ids:
                        found = False
                        for pl_library in self.libraries:
                            if input_id in pl_library.movie_map:
                                found = True
                                rating_keys = pl_library.movie_map[input_id]
                                break
                        if not found and input_id not in self.missing_movies:
                            self.missing_movies.append(input_id)
                elif id_type in ["tvdb", "tmdb_show"] and not self.parts_collection:
                    if id_type == "tmdb_show":
                        try:
                            tvdb_id = self.config.Convert.tmdb_to_tvdb(input_id, fail=True)
                        except Failed as e:
                            logger.warning(e)
                            continue
                    else:
                        tvdb_id = int(input_id)
                    if tvdb_id not in self.ignore_ids:
                        found = False
                        for pl_library in self.libraries:
                            if tvdb_id in pl_library.show_map:
                                found = True
                                rating_keys = pl_library.show_map[tvdb_id]
                                break
                        if not found and tvdb_id not in self.missing_shows:
                            self.missing_shows.append(input_id)
                elif id_type == "tvdb_season" and (self.collection_level == "season" or self.playlist):
                    tvdb_id, season_num = input_id.split("_")
                    tvdb_id = int(tvdb_id)
                    found = False
                    for pl_library in self.libraries:
                        if tvdb_id in pl_library.show_map:
                            found = True
                            show_item = pl_library.fetchItem(pl_library.show_map[tvdb_id][0])
                            try:
                                season_obj = show_item.season(season=int(season_num))
                                if self.playlist:
                                    items.extend(season_obj.episodes())
                                else:
                                    items.append(season_obj)
                            except NotFound:
                                self.missing_parts.append(f"{show_item.title} Season: {season_num} Missing")
                            break
                    if not found and tvdb_id not in self.missing_shows:
                        self.missing_shows.append(tvdb_id)
                elif id_type == "tvdb_episode" and (self.collection_level == "episode" or self.playlist):
                    tvdb_id, season_num, episode_num = input_id.split("_")
                    tvdb_id = int(tvdb_id)
                    found = False
                    for pl_library in self.libraries:
                        if tvdb_id in pl_library.show_map:
                            found = True
                            show_item = pl_library.fetchItem(pl_library.show_map[tvdb_id][0])
                            try:
                                items.append(show_item.episode(season=int(season_num), episode=int(episode_num)))
                            except NotFound:
                                self.missing_parts.append(f"{show_item.title} Season: {season_num} Episode: {episode_num} Missing")
                    if not found and tvdb_id not in self.missing_shows and self.do_missing:
                        self.missing_shows.append(tvdb_id)
                else:
                    continue

                if not isinstance(rating_keys, list):
                    rating_keys = [rating_keys]
                for rk in rating_keys:
                    try:
                        item = self.fetch_item(rk)
                        if self.playlist and isinstance(item, (Show, Season)):
                            items.extend(item.episodes())
                        else:
                            items.append(item)
                    except Failed as e:
                        logger.error(e)
            logger.exorcise()
        if not items:
            return None
        name = self.obj.title if self.obj else self.name
        total = len(items)
        max_length = len(str(total))
        if (self.filters or self.tmdb_filters) and self.details["show_filtered"] is True:
            logger.info("")
            logger.info("Filtering Builders:")
        for i, item in enumerate(items, 1):
            if not isinstance(item, (Movie, Show, Season, Episode, Artist, Album, Track)):
                logger.error(f"{self.Type} Error: Item: {item} is an invalid type")
                continue
            if item not in self.added_items:
                if item.ratingKey in self.filtered_keys:
                    if self.details["show_filtered"] is True:
                        logger.info(f"{name} {self.Type} | X | {self.filtered_keys[item.ratingKey]}")
                else:
                    current_title = util.item_title(item)
                    if self.check_filters(item, f"{(' ' * (max_length - len(str(i))))}{i}/{total}"):
                        self.added_items.append(item)
                    else:
                        self.filtered_keys[item.ratingKey] = current_title
                        if self.details["show_filtered"] is True:
                            logger.info(f"{name} {self.Type} | X | {current_title}")

    def build_filter(self, method, plex_filter, display=False, default_sort="title.asc", type_override=None):
        if display:
            logger.info("")
            logger.info(f"Validating Method: {method}")
        if plex_filter is None:
            raise Failed(f"{self.Type} Error: {method} attribute is blank")
        if not isinstance(plex_filter, dict):
            raise Failed(f"{self.Type} Error: {method} must be a dictionary: {plex_filter}")
        if display:
            logger.debug(f"Value: {plex_filter}")

        filter_alias = {m.lower(): m for m in plex_filter}

        if "any" in filter_alias and "all" in filter_alias:
            raise Failed(f"{self.Type} Error: Cannot have more then one base")

        if type_override:
            sort_type = type_override
        elif "type" in filter_alias and self.library.is_show:
            if plex_filter[filter_alias["type"]] not in ["shows", "seasons", "episodes"]:
                raise Failed(f"{self.Type} Error: type: {plex_filter[filter_alias['type']]} is invalid, must be either shows, season, or episodes")
            sort_type = plex_filter[filter_alias["type"]]
        elif "type" in filter_alias and self.library.is_music:
            if plex_filter[filter_alias["type"]] not in ["artists", "albums", "tracks"]:
                raise Failed(f"{self.Type} Error: type: {plex_filter[filter_alias['type']]} is invalid, must be either artists, albums, or tracks")
            sort_type = plex_filter[filter_alias["type"]]
        elif self.library.is_show:
            sort_type = "shows"
        elif self.library.is_music:
            sort_type = "artists"
        else:
            sort_type = "movies"
        ms = method.split("_")
        filter_details = f"{ms[0].capitalize()} {sort_type.capitalize()[:-1]} {ms[1].capitalize()}\n"
        type_key, sorts = plex.sort_types[sort_type]

        sort = default_sort
        if "sort_by" in filter_alias:
            if plex_filter[filter_alias["sort_by"]] is None:
                raise Failed(f"{self.Type} Error: sort_by attribute is blank")
            if plex_filter[filter_alias["sort_by"]] not in sorts:
                raise Failed(f"{self.Type} Error: sort_by: {plex_filter[filter_alias['sort_by']]} is invalid")
            sort = plex_filter[filter_alias["sort_by"]]
        filter_details += f"Sort By: {sort}\n"

        limit = None
        if "limit" in filter_alias:
            if plex_filter[filter_alias["limit"]] is None:
                raise Failed(f"{self.Type} Error: limit attribute is blank")
            elif str(plex_filter[filter_alias["limit"]]).lower() == "all":
                filter_details += "Limit: all\n"
            elif not isinstance(plex_filter[filter_alias["limit"]], int) or plex_filter[filter_alias["limit"]] < 1:
                raise Failed(f"{self.Type} Error: limit attribute must be an integer greater then 0")
            else:
                limit = plex_filter[filter_alias["limit"]]
                filter_details += f"Limit: {limit}\n"

        validate = True
        if "validate" in filter_alias:
            if plex_filter[filter_alias["validate"]] is None:
                raise Failed(f"{self.Type} Error: validate attribute is blank")
            if not isinstance(plex_filter[filter_alias["validate"]], bool):
                raise Failed(f"{self.Type} Error: validate attribute must be either true or false")
            validate = plex_filter[filter_alias["validate"]]
            filter_details += f"Validate: {validate}\n"

        def _filter(filter_dict, is_all=True, level=1):
            output = ""
            display_out = f"\n{'  ' * level}Match {'all' if is_all else 'any'} of the following:"
            level += 1
            indent = f"\n{'  ' * level}"
            conjunction = f"{'and' if is_all else 'or'}=1&"
            for _key, _data in filter_dict.items():
                attr, modifier, final_attr = self._split(_key)

                def build_url_arg(arg, mod=None, arg_s=None, mod_s=None):
                    arg_key = plex.search_translation[attr] if attr in plex.search_translation else attr
                    arg_key = plex.show_translation[arg_key] if self.library.is_show and arg_key in plex.show_translation else arg_key
                    if mod is None:
                        mod = plex.modifier_translation[modifier] if modifier in plex.modifier_translation else modifier
                    if arg_s is None:
                        arg_s = arg
                    if attr in plex.string_attributes and modifier in ["", ".not"]:
                        mod_s = "does not contain" if modifier == ".not" else "contains"
                    elif mod_s is None:
                        mod_s = util.mod_displays[modifier]
                    param_s = plex.search_display[attr] if attr in plex.search_display else attr.title().replace('_', ' ')
                    display_line = f"{indent}{param_s} {mod_s} {arg_s}"
                    return f"{arg_key}{mod}={arg}&", display_line

                error = None
                if final_attr not in plex.searches and not final_attr.startswith(("any", "all")):
                    error = f"{self.Type} Error: {final_attr} is not a valid {method} attribute"
                elif self.library.is_show and final_attr in plex.movie_only_searches:
                    error = f"{self.Type} Error: {final_attr} {method} attribute only works for movie libraries"
                elif self.library.is_movie and final_attr in plex.show_only_searches:
                    error = f"{self.Type} Error: {final_attr} {method} attribute only works for show libraries"
                elif self.library.is_music and final_attr not in plex.music_searches + ["all", "any"]:
                    error = f"{self.Type} Error: {final_attr} {method} attribute does not work for music libraries"
                elif not self.library.is_music and final_attr in plex.music_searches:
                    error = f"{self.Type} Error: {final_attr} {method} attribute only works for music libraries"
                elif _data is not False and not _data:
                    error = f"{self.Type} Error: {final_attr} {method} attribute is blank"
                else:
                    if final_attr.startswith(("any", "all")):
                        dicts = util.get_list(_data)
                        results = ""
                        display_add = ""
                        for dict_data in dicts:
                            if not isinstance(dict_data, dict):
                                raise Failed(f"{self.Type} Error: {attr} must be either a dictionary or list of dictionaries")
                            inside_filter, inside_display = _filter(dict_data, is_all=attr == "all", level=level)
                            if len(inside_filter) > 0:
                                display_add += inside_display
                                results += f"{conjunction if len(results) > 0 else ''}push=1&{inside_filter}pop=1&"
                    else:
                        validation = self.validate_attribute(attr, modifier, final_attr, _data, validate, pairs=True)
                        if validation is not False and not validation:
                            continue
                        elif attr in plex.date_attributes and modifier in ["", ".not"]:
                            last_text = "is not in the last" if modifier == ".not" else "is in the last"
                            last_mod = "%3E%3E" if modifier == "" else "%3C%3C"
                            results, display_add = build_url_arg(f"-{validation}d", mod=last_mod, arg_s=f"{validation} Days", mod_s=last_text)
                        elif attr == "duration" and modifier in [".gt", ".gte", ".lt", ".lte"]:
                            results, display_add = build_url_arg(validation * 60000)
                        elif attr in plex.boolean_attributes:
                            bool_mod = "" if validation else "!"
                            bool_arg = "true" if validation else "false"
                            results, display_add = build_url_arg(1, mod=bool_mod, arg_s=bool_arg, mod_s="is")
                        elif (attr in plex.tag_attributes + plex.string_attributes + plex.year_attributes) and modifier in ["", ".is", ".isnot", ".not", ".begins", ".ends"]:
                            results = ""
                            display_add = ""
                            for og_value, result in validation:
                                built_arg = build_url_arg(quote(str(result)) if attr in plex.string_attributes else result, arg_s=og_value)
                                display_add += built_arg[1]
                                results += f"{conjunction if len(results) > 0 else ''}{built_arg[0]}"
                        else:
                            results, display_add = build_url_arg(validation)
                    display_out += display_add
                    output += f"{conjunction if len(output) > 0 else ''}{results}"
                if error:
                    if validate:
                        raise Failed(error)
                    else:
                        logger.error(error)
                        continue
            return output, display_out

        if "any" not in filter_alias and "all" not in filter_alias:
            base_dict = {}
            any_dicts = []
            for alias_key, alias_value in filter_alias.items():
                _, _, final = self._split(alias_key)
                if final in plex.and_searches:
                    base_dict[alias_value[:-4]] = plex_filter[alias_value]
                elif final in plex.or_searches:
                    any_dicts.append({alias_value: plex_filter[alias_value]})
                elif final in plex.searches:
                    base_dict[alias_value] = plex_filter[alias_value]
            if len(any_dicts) > 0:
                base_dict["any"] = any_dicts
            base_all = True
            if len(base_dict) == 0:
                raise Failed(f"{self.Type} Error: Must have either any or all as a base for {method}")
        else:
            base = "all" if "all" in filter_alias else "any"
            base_all = base == "all"
            if plex_filter[filter_alias[base]] is None:
                raise Failed(f"{self.Type} Error: {base} attribute is blank")
            if not isinstance(plex_filter[filter_alias[base]], dict):
                raise Failed(f"{self.Type} Error: {base} must be a dictionary: {plex_filter[filter_alias[base]]}")
            base_dict = plex_filter[filter_alias[base]]
        built_filter, filter_text = _filter(base_dict, is_all=base_all)
        filter_details = f"{filter_details}Filter:{filter_text}"
        if len(built_filter) > 0:
            final_filter = built_filter[:-1] if base_all else f"push=1&{built_filter}pop=1"
            filter_url = f"?type={type_key}&{f'limit={limit}&' if limit else ''}sort={sorts[sort]}&{final_filter}"
        else:
            raise Failed(f"{self.Type} Error: No Filter Created")

        return type_key, filter_details, filter_url

    def validate_attribute(self, attribute, modifier, final, data, validate, pairs=False):
        def smart_pair(list_to_pair):
            return [(t, t) for t in list_to_pair] if pairs else list_to_pair
        if modifier == ".regex":
            regex_list = util.get_list(data, split=False)
            valid_regex = []
            for reg in regex_list:
                try:
                    re.compile(reg)
                    valid_regex.append(reg)
                except re.error:
                    logger.stacktrace()
                    err = f"{self.Type} Error: Regular Expression Invalid: {reg}"
                    if validate:
                        raise Failed(err)
                    else:
                        logger.error(err)
            return valid_regex
        elif attribute in plex.string_attributes + string_filters and modifier in ["", ".not", ".is", ".isnot", ".begins", ".ends"]:
            return smart_pair(util.get_list(data, split=False))
        elif attribute == "origin_country":
            return util.get_list(data, upper=True)
        elif attribute in ["original_language", "tmdb_keyword"]:
            return util.get_list(data, lower=True)
        elif attribute in ["filepath", "tmdb_genre"]:
            return util.get_list(data)
        elif attribute == "history":
            try:
                return util.parse(self.Type, final, data, datatype="int", maximum=30)
            except Failed:
                if str(data).lower() in ["day", "month"]:
                    return data.lower()
            raise Failed(f"{self.Type} Error: history attribute invalid: {data} must be a number between 1-30, day, or month")
        elif attribute == "tmdb_type":
            return util.parse(self.Type, final, data, datatype="commalist", options=[v for k, v in discover_types.items()])
        elif attribute == "tmdb_status":
            return util.parse(self.Type, final, data, datatype="commalist", options=[v for k, v in discover_status.items()])
        elif attribute in plex.tag_attributes and modifier in ["", ".not"]:
            if attribute in plex.tmdb_attributes:
                final_values = []
                for value in util.get_list(data):
                    if value.lower() == "tmdb" and "tmdb_person" in self.details:
                        for name in self.details["tmdb_person"]:
                            final_values.append(name)
                    else:
                        final_values.append(value)
            else:
                final_values = util.get_list(data)
            use_title = not pairs
            search_choices, names = self.library.get_search_choices(attribute, title=use_title)
            valid_list = []
            for value in final_values:
                if str(value).lower() in search_choices:
                    if pairs:
                        valid_list.append((value, search_choices[str(value).lower()]))
                    else:
                        valid_list.append(search_choices[str(value).lower()])
                else:
                    error = f"Plex Error: {attribute}: {value} not found"
                    if self.details["show_options"]:
                        error += f"\nOptions: {names}"
                    if validate:
                        raise Failed(error)
                    else:
                        logger.error(error)
            return valid_list
        elif attribute in plex.date_attributes and modifier in [".before", ".after"]:
            if data == "today":
                return datetime.strftime(datetime.now(), "%Y-%m-%d")
            else:
                return util.validate_date(data, final, return_as="%Y-%m-%d")
        elif attribute in plex.year_attributes + ["tmdb_year"] and modifier in ["", ".not"]:
            final_years = []
            values = util.get_list(data)
            for value in values:
                final_years.append(util.parse(self.Type, final, value, datatype="int"))
            return smart_pair(final_years)
        elif (attribute in plex.number_attributes + plex.date_attributes + plex.year_attributes + ["tmdb_year"] and modifier in ["", ".not", ".gt", ".gte", ".lt", ".lte"]) \
                or (attribute in plex.tag_attributes and modifier in [".count_gt", ".count_gte", ".count_lt", ".count_lte"]):
            return util.parse(self.Type, final, data, datatype="int")
        elif attribute in plex.float_attributes and modifier in [".gt", ".gte", ".lt", ".lte"]:
            return util.parse(self.Type, final, data, datatype="float", minimum=0, maximum=None if attribute == "duration" else 10)
        elif attribute in plex.boolean_attributes + boolean_filters:
            return util.parse(self.Type, attribute, data, datatype="bool")
        else:
            raise Failed(f"{self.Type} Error: {final} attribute not supported")

    def _split(self, text):
        attribute, modifier = os.path.splitext(str(text).lower())
        attribute = method_alias[attribute] if attribute in method_alias else attribute
        modifier = modifier_alias[modifier] if modifier in modifier_alias else modifier

        if attribute == "add_to_arr":
            attribute = "radarr_add_missing" if self.library.is_movie else "sonarr_add_missing"
        elif attribute in ["arr_tag", "arr_folder"]:
            attribute = f"{'rad' if self.library.is_movie else 'son'}{attribute}"
        elif attribute in plex.date_attributes and modifier in [".gt", ".gte"]:
            modifier = ".after"
        elif attribute in plex.date_attributes and modifier in [".lt", ".lte"]:
            modifier = ".before"
        final = f"{attribute}{modifier}"
        if text != final:
            logger.warning(f"Collection Warning: {text} attribute will run as {final}")
        return attribute, modifier, final

    def fetch_item(self, item):
        try:
            current = self.library.fetchItem(item.ratingKey if isinstance(item, (Movie, Show, Season, Episode, Artist, Album, Track)) else int(item))
            if not isinstance(current, (Movie, Show, Season, Episode, Artist, Album, Track)):
                raise NotFound
            return current
        except (BadRequest, NotFound):
            raise Failed(f"Plex Error: Item {item} not found")

    def add_to_collection(self):
        logger.info("")
        logger.separator(f"Adding to {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        name, collection_items = self.library.get_collection_name_and_items(self.obj if self.obj else self.name, self.smart_label_collection)
        total = self.limit if self.limit and len(self.added_items) > self.limit else len(self.added_items)
        spacing = len(str(total)) * 2 + 1
        amount_added = 0
        amount_unchanged = 0
        playlist_adds = []
        for i, item in enumerate(self.added_items, 1):
            if self.limit and amount_added + self.beginning_count - len([r for _, r in self.remove_item_map.items() if r is not None]) >= self.limit:
                logger.info(f"{self.Type} Limit reached")
                self.added_items = self.added_items[:i-1]
                break
            current_operation = "=" if item in collection_items else "+"
            number_text = f"{i}/{total}"
            logger.info(f"{number_text:>{spacing}} | {name} {self.Type} | {current_operation} | {util.item_title(item)}")
            if item in collection_items:
                self.remove_item_map[item.ratingKey] = None
                amount_unchanged += 1
            else:
                if self.playlist:
                    playlist_adds.append(item)
                else:
                    self.library.alter_collection(item, name, smart_label_collection=self.smart_label_collection)
                amount_added += 1
                if self.details["changes_webhooks"]:
                    if item.ratingKey in self.library.movie_rating_key_map:
                        add_id = self.library.movie_rating_key_map[item.ratingKey]
                    elif item.ratingKey in self.library.show_rating_key_map:
                        add_id = self.library.show_rating_key_map[item.ratingKey]
                    else:
                        add_id = None
                    self.notification_additions.append(util.item_set(item, add_id))
        if self.playlist and playlist_adds and not self.obj:
            self.obj = self.library.create_playlist(self.name, playlist_adds)
            logger.info("")
            logger.info(f"Playlist: {self.name} created")
        elif self.playlist and playlist_adds:
            self.obj.addItems(playlist_adds)
        logger.exorcise()
        logger.info("")
        logger.info(f"{total} {self.collection_level.capitalize()}{'s' if total > 1 else ''} Processed")
        return amount_added, amount_unchanged

    def sync_collection(self):
        amount_removed = 0
        playlist_removes = []
        items = [item for _, item in self.remove_item_map.items() if item is not None]
        if items:
            logger.info("")
            logger.separator(f"Removed from {self.name} {self.Type}", space=False, border=False)
            logger.info("")
            total = len(items)
            spacing = len(str(total)) * 2 + 1
            for i, item in enumerate(items, 1):
                self.library.reload(item)
                number_text = f"{i}/{total}"
                logger.info(f"{number_text:>{spacing}} | {self.name} {self.Type} | - | {util.item_title(item)}")
                if self.playlist:
                    playlist_removes.append(item)
                else:
                    self.library.alter_collection(item, self.name, smart_label_collection=self.smart_label_collection, add=False)
                amount_removed += 1
                if self.details["changes_webhooks"]:
                    if item.ratingKey in self.library.movie_rating_key_map:
                        remove_id = self.library.movie_rating_key_map[item.ratingKey]
                    elif item.ratingKey in self.library.show_rating_key_map:
                        remove_id = self.library.show_rating_key_map[item.ratingKey]
                    else:
                        remove_id = None
                    self.notification_removals.append(util.item_set(item, remove_id))
            if self.playlist and playlist_removes:
                self.obj.reload()
                self.obj.removeItems(playlist_removes)
            logger.info("")
            logger.info(f"{amount_removed} {self.collection_level.capitalize()}{'s' if amount_removed == 1 else ''} Removed")
        return amount_removed

    def check_tmdb_filter(self, item_id, is_movie, item=None, check_released=False):
        if self.tmdb_filters or check_released:
            try:
                if item is None:
                    if is_movie:
                        item = self.config.TMDb.get_movie(item_id)
                    else:
                        item = self.config.TMDb.get_show(self.config.Convert.tvdb_to_tmdb(item_id))
                if check_released:
                    date_to_check = item.release_date if is_movie else item.first_air_date
                    if not date_to_check or date_to_check > self.current_time:
                        return False
                for filter_method, filter_data in self.tmdb_filters:
                    filter_attr, modifier, filter_final = self._split(filter_method)
                    if filter_attr in ["tmdb_status", "tmdb_type", "original_language"]:
                        if filter_attr == "tmdb_status":
                            check_value = discover_status[item.status]
                        elif filter_attr == "tmdb_type":
                            check_value = discover_types[item.type]
                        elif filter_attr == "original_language":
                            check_value = item.language_iso
                        else:
                            raise Failed
                        if (modifier == ".not" and check_value in filter_data) or (modifier == "" and check_value not in filter_data):
                            return False
                    elif filter_attr in ["first_episode_aired", "last_episode_aired"]:
                        tmdb_date = None
                        if filter_attr == "first_episode_aired":
                            tmdb_date = item.first_air_date
                        elif filter_attr == "last_episode_aired":
                            tmdb_date = item.last_air_date
                        if util.is_date_filter(tmdb_date, modifier, filter_data, filter_final, self.current_time):
                            return False
                    elif modifier in [".gt", ".gte", ".lt", ".lte"]:
                        attr = None
                        if filter_attr == "tmdb_vote_count":
                            attr = item.vote_count
                        elif filter_attr == "tmdb_year":
                            attr = item.release_date.year if is_movie else item.first_air_date.year
                        if util.is_number_filter(attr, modifier, filter_data):
                            return False
                    elif filter_attr in ["tmdb_genre", "tmdb_keyword", "origin_country"]:
                        if filter_attr == "tmdb_genre":
                            attrs = item.genres
                        elif filter_attr == "tmdb_keyword":
                            attrs = item.keywords
                        elif filter_attr == "origin_country":
                            attrs = [c.iso_3166_1 for c in item.countries]
                        else:
                            raise Failed
                        if (not list(set(filter_data) & set(attrs)) and modifier == "") \
                                or (list(set(filter_data) & set(attrs)) and modifier == ".not"):
                            return False
                    elif filter_attr == "tmdb_title":
                        if util.is_string_filter([item.title], modifier, filter_data):
                            return False
            except Failed:
                return False
        return True

    def check_filters(self, item, display):
        if (self.filters or self.tmdb_filters) and not self.details["only_filter_missing"]:
            logger.ghost(f"Filtering {display} {item.title}")
            if self.tmdb_filters and isinstance(item, (Movie, Show)):
                if item.ratingKey not in self.library.movie_rating_key_map and item.ratingKey not in self.library.show_rating_key_map:
                    logger.warning(f"Filter Error: No {'TMDb' if self.library.is_movie else 'TVDb'} ID found for {item.title}")
                    return False
                try:
                    if item.ratingKey in self.library.movie_rating_key_map:
                        t_id = self.library.movie_rating_key_map[item.ratingKey]
                    else:
                        t_id = self.library.show_rating_key_map[item.ratingKey]
                except Failed as e:
                    logger.error(e)
                    return False
                if not self.check_tmdb_filter(t_id, item.ratingKey in self.library.movie_rating_key_map):
                    return False
            for filter_method, filter_data in self.filters:
                filter_attr, modifier, filter_final = self._split(filter_method)
                filter_actual = filter_translation[filter_attr] if filter_attr in filter_translation else filter_attr
                item_type = self.collection_level
                if self.collection_level == "item":
                    if isinstance(item, Movie):
                        item_type = "movie"
                    elif isinstance(item, Show):
                        item_type = "show"
                    elif isinstance(item, Season):
                        item_type = "season"
                    elif isinstance(item, Episode):
                        item_type = "episode"
                    elif isinstance(item, Artist):
                        item_type = "artist"
                    elif isinstance(item, Album):
                        item_type = "album"
                    elif isinstance(item, Track):
                        item_type = "track"
                    else:
                        continue
                if filter_attr not in filters[item_type]:
                    continue
                elif filter_attr in date_filters:
                    if util.is_date_filter(getattr(item, filter_actual), modifier, filter_data, filter_final, self.current_time):
                        return False
                elif filter_attr in string_filters:
                    values = []
                    if filter_attr == "audio_track_title":
                        for media in item.media:
                            for part in media.parts:
                                values.extend([a.title for a in part.audioStreams() if a.title])
                    elif filter_attr == "filepath":
                        values = [loc for loc in item.locations]
                    else:
                        values = [getattr(item, filter_actual)]
                    if util.is_string_filter(values, modifier, filter_data):
                        return False
                elif filter_attr in boolean_filters:
                    filter_check = False
                    if filter_attr == "has_collection":
                        filter_check = len(item.collections) > 0
                    elif filter_attr == "has_overlay":
                        for label in item.labels:
                            if label.tag.lower().endswith(" overlay"):
                                filter_check = True
                                break
                    elif filter_attr == "has_dolby_vision":
                        for media in item.media:
                            for part in media.parts:
                                for stream in part.videoStreams():
                                    if stream.DOVIPresent:
                                        filter_check = True
                                        break
                    if util.is_boolean_filter(filter_data, filter_check):
                        return False
                elif filter_attr == "history":
                    item_date = item.originallyAvailableAt
                    if item_date is None:
                        return False
                    elif filter_data == "day":
                        if item_date.month != self.current_time.month or item_date.day != self.current_time.day:
                            return False
                    elif filter_data == "month":
                        if item_date.month != self.current_time.month:
                            return False
                    else:
                        date_match = False
                        for i in range(filter_data):
                            check_date = self.current_time - timedelta(days=i)
                            if item_date.month == check_date.month and item_date.day == check_date.day:
                                date_match = True
                        if date_match is False:
                            return False
                elif modifier in [".gt", ".gte", ".lt", ".lte", ".count_gt", ".count_gte", ".count_lt", ".count_lte"]:
                    divider = 60000 if filter_attr == "duration" else 1
                    test_number = getattr(item, filter_actual)
                    if modifier in [".count_gt", ".count_gte", ".count_lt", ".count_lte"]:
                        test_number = len(test_number) if test_number else 0
                        modifier = f".{modifier[7:]}"
                    if test_number is None or util.is_number_filter(test_number / divider, modifier, filter_data):
                        return False
                else:
                    attrs = []
                    if filter_attr in ["resolution", "audio_language", "subtitle_language"]:
                        for media in item.media:
                            if filter_attr == "resolution":
                                attrs.append(media.videoResolution)
                            for part in media.parts:
                                if filter_attr == "audio_language":
                                    attrs.extend([a.language for a in part.audioStreams()])
                                if filter_attr == "subtitle_language":
                                    attrs.extend([s.language for s in part.subtitleStreams()])
                    elif filter_attr in ["content_rating", "year", "rating"]:
                        attrs = [getattr(item, filter_actual)]
                    elif filter_attr in ["actor", "country", "director", "genre", "label", "producer", "writer", "collection"]:
                        attrs = [attr.tag for attr in getattr(item, filter_actual)]
                    else:
                        raise Failed(f"Filter Error: filter: {filter_final} not supported")
                    if (not list(set(filter_data) & set(attrs)) and modifier == "") \
                            or (list(set(filter_data) & set(attrs)) and modifier == ".not"):
                        return False
            logger.ghost(f"Filtering {display} {item.title}")
        return True

    def run_missing(self):
        added_to_radarr = 0
        added_to_sonarr = 0
        if len(self.missing_movies) > 0:
            if self.details["show_missing"] is True:
                logger.info("")
                logger.separator(f"Missing Movies from Library: {self.library.name}", space=False, border=False)
                logger.info("")
            missing_movies_with_names = []
            for missing_id in self.missing_movies:
                try:
                    movie = self.config.TMDb.get_movie(missing_id)
                except Failed as e:
                    logger.error(e)
                    continue
                current_title = f"{movie.title} ({movie.release_date.year})" if movie.release_date else movie.title
                if self.check_tmdb_filter(missing_id, True, item=movie, check_released=self.details["missing_only_released"]):
                    missing_movies_with_names.append((current_title, missing_id))
                    if self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | ? | {current_title} (TMDb: {missing_id})")
                else:
                    if self.details["show_filtered"] is True and self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | X | {current_title} (TMDb: {missing_id})")
            logger.info("")
            logger.info(f"{len(missing_movies_with_names)} Movie{'s' if len(missing_movies_with_names) > 1 else ''} Missing")
            if len(missing_movies_with_names) > 0:
                if self.details["save_missing"] is True:
                    self.library.add_missing(self.name, missing_movies_with_names, True)
                if self.run_again or (self.library.Radarr and (self.radarr_details["add_missing"] or "item_radarr_tag" in self.item_details)):
                    missing_tmdb_ids = [missing_id for title, missing_id in missing_movies_with_names]
                    if self.library.Radarr:
                        if self.radarr_details["add_missing"]:
                            try:
                                added = self.library.Radarr.add_tmdb(missing_tmdb_ids, **self.radarr_details)
                                self.added_to_radarr.extend([{"title": movie.title, "id": movie.tmdbId} for movie in added])
                                added_to_radarr += len(added)
                            except Failed as e:
                                logger.error(e)
                        if "item_radarr_tag" in self.item_details:
                            try:
                                self.library.Radarr.edit_tags(missing_tmdb_ids, self.item_details["item_radarr_tag"], self.item_details["apply_tags"])
                            except Failed as e:
                                logger.error(e)
                    if self.run_again:
                        self.run_again_movies.extend(missing_tmdb_ids)
        if len(self.missing_shows) > 0 and self.library.is_show:
            if self.details["show_missing"] is True:
                logger.info("")
                logger.separator(f"Missing Shows from Library: {self.name}", space=False, border=False)
                logger.info("")
            missing_shows_with_names = []
            for missing_id in self.missing_shows:
                try:
                    show = self.config.TVDb.get_series(missing_id)
                except Failed as e:
                    logger.error(e)
                    continue
                if self.check_tmdb_filter(missing_id, False, check_released=self.details["missing_only_released"]):
                    missing_shows_with_names.append((show.title, missing_id))
                    if self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | ? | {show.title} (TVDb: {missing_id})")
                else:
                    if self.details["show_filtered"] is True and self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | X | {show.title} (TVDb: {missing_id})")
            logger.info("")
            logger.info(f"{len(missing_shows_with_names)} Show{'s' if len(missing_shows_with_names) > 1 else ''} Missing")
            if len(missing_shows_with_names) > 0:
                if self.details["save_missing"] is True:
                    self.library.add_missing(self.name, missing_shows_with_names, False)
                if self.run_again or (self.library.Sonarr and (self.sonarr_details["add_missing"] or "item_sonarr_tag" in self.item_details)):
                    missing_tvdb_ids = [missing_id for title, missing_id in missing_shows_with_names]
                    if self.library.Sonarr:
                        if self.sonarr_details["add_missing"]:
                            try:
                                added = self.library.Sonarr.add_tvdb(missing_tvdb_ids, **self.sonarr_details)
                                self.added_to_sonarr.extend([{"title": show.title, "id": show.tvdbId} for show in added])
                                added_to_sonarr += len(added)
                            except Failed as e:
                                logger.error(e)
                        if "item_sonarr_tag" in self.item_details:
                            try:
                                self.library.Sonarr.edit_tags(missing_tvdb_ids, self.item_details["item_sonarr_tag"], self.item_details["apply_tags"])
                            except Failed as e:
                                logger.error(e)
                    if self.run_again:
                        self.run_again_shows.extend(missing_tvdb_ids)
        if len(self.missing_parts) > 0 and self.library.is_show and self.details["save_missing"] is True:
            for missing in self.missing_parts:
                logger.info(f"{self.name} {self.Type} | X | {missing}")
        return added_to_radarr, added_to_sonarr

    def load_collection_items(self):
        if self.build_collection and self.obj:
            self.items = self.library.get_collection_items(self.obj, self.smart_label_collection)
        elif not self.build_collection:
            logger.info("")
            logger.separator(f"Items Found for {self.name} {self.Type}", space=False, border=False)
            logger.info("")
            self.items = self.added_items
        if not self.items:
            raise Failed(f"Plex Error: No {self.Type} items found")

    def update_item_details(self):
        logger.info("")
        logger.separator(f"Updating Details of the Items in {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        overlay = None
        overlay_folder = None
        overlay_name = ""
        rating_keys = []
        if "item_overlay" in self.item_details:
            overlay_name = self.item_details["item_overlay"]
            if self.config.Cache:
                cache_keys = self.config.Cache.query_image_map_overlay(self.library.image_table_name, overlay_name)
                if cache_keys:
                    for rating_key in cache_keys:
                        try:
                            item = self.fetch_item(rating_key)
                        except Failed as e:
                            logger.error(e)
                            continue
                        if isinstance(item, (Movie, Show)):
                            self.library.edit_tags("label", item, add_tags=[f"{overlay_name} Overlay"])
                    self.config.Cache.update_remove_overlay(self.library.image_table_name, overlay_name)
            rating_keys = [int(item.ratingKey) for item in self.library.get_labeled_items(f"{overlay_name} Overlay")]
            overlay_folder = os.path.join(self.config.default_dir, "overlays", overlay_name)
            overlay_image = Image.open(os.path.join(overlay_folder, "overlay.png")).convert("RGBA")
            overlay = (overlay_name, overlay_folder, overlay_image)

        revert = "revert_overlay" in self.item_details
        if revert:
            overlay = None

        add_tags = self.item_details["item_label"] if "item_label" in self.item_details else None
        remove_tags = self.item_details["item_label.remove"] if "item_label.remove" in self.item_details else None
        sync_tags = self.item_details["item_label.sync"] if "item_label.sync" in self.item_details else None

        if "non_item_remove_label" in self.item_details:
            rk_compare = [item.ratingKey for item in self.items]
            for remove_label in self.item_details["non_item_remove_label"]:
                for non_item in self.library.get_labeled_items(remove_label):
                    if non_item.ratingKey not in rk_compare:
                        self.library.edit_tags("label", non_item, remove_tags=[remove_label])

        tmdb_paths = []
        tvdb_paths = []
        for item in self.items:
            if int(item.ratingKey) in rating_keys and not revert:
                rating_keys.remove(int(item.ratingKey))
            if "item_assets" in self.item_details or overlay is not None:
                try:
                    self.library.find_assets(item, overlay=overlay, folders=self.details["asset_folders"], create=self.details["create_asset_folders"])
                except Failed as e:
                    logger.error(e)
            self.library.edit_tags("label", item, add_tags=add_tags, remove_tags=remove_tags, sync_tags=sync_tags)
            path = os.path.dirname(str(item.locations[0])) if self.library.is_movie else str(item.locations[0])
            if self.library.Radarr and item.ratingKey in self.library.movie_rating_key_map:
                path = path.replace(self.library.Radarr.plex_path, self.library.Radarr.radarr_path)
                path = path[:-1] if path.endswith(('/', '\\')) else path
                tmdb_paths.append((self.library.movie_rating_key_map[item.ratingKey], path))
            if self.library.Sonarr and item.ratingKey in self.library.show_rating_key_map:
                path = path.replace(self.library.Sonarr.plex_path, self.library.Sonarr.sonarr_path)
                path = path[:-1] if path.endswith(('/', '\\')) else path
                tvdb_paths.append((self.library.show_rating_key_map[item.ratingKey], path))
            advance_edits = {}
            if hasattr(item, "preferences"):
                prefs = [p.id for p in item.preferences()]
                for method_name, method_data in self.item_details.items():
                    if method_name in plex.item_advance_keys:
                        key, options = plex.item_advance_keys[method_name]
                        if key in prefs and getattr(item, key) != options[method_data]:
                            advance_edits[key] = options[method_data]
            self.library.edit_item(item, item.title, self.collection_level.capitalize(), advance_edits, advanced=True)

            if "item_tmdb_season_titles" in self.item_details and item.ratingKey in self.library.show_rating_key_map:
                try:
                    tmdb_id = self.config.Convert.tvdb_to_tmdb(self.library.show_rating_key_map[item.ratingKey])
                    names = {s.season_number: s.name for s in self.config.TMDb.get_show(tmdb_id).seasons}
                    for season in self.library.query(item.seasons):
                        if season.index in names and season.title != names[season.index]:
                            season.editTitle(names[season.index])
                except Failed as e:
                    logger.error(e)

            # Locking should come before refreshing since refreshing can change metadata (i.e. if specified to both lock
            # background/poster and also refreshing, assume that the item background/poster should be kept)
            if "item_lock_background" in self.item_details:
                self.library.query(item.lockArt if self.item_details["item_lock_background"] else item.unlockArt)
            if "item_lock_poster" in self.item_details:
                self.library.query(item.lockPoster if self.item_details["item_lock_poster"] else item.unlockPoster)
            if "item_lock_title" in self.item_details:
                self.library.edit_query(item, {"title.locked": 1 if self.item_details["item_lock_title"] else 0})
            if "item_refresh" in self.item_details:
                delay = self.item_details["item_refresh_delay"] if "item_refresh_delay" in self.item_details else self.library.item_refresh_delay
                if delay > 0:
                    time.sleep(delay)
                self.library.query(item.refresh)

        if self.library.Radarr and tmdb_paths:
            if "item_radarr_tag" in self.item_details:
                self.library.Radarr.edit_tags([t[0] if isinstance(t, tuple) else t for t in tmdb_paths], self.item_details["item_radarr_tag"], self.item_details["apply_tags"])
            if self.radarr_details["add_existing"]:
                added = self.library.Radarr.add_tmdb(tmdb_paths, **self.radarr_details)
                self.added_to_radarr.extend([{"title": movie.title, "id": movie.tmdbId} for movie in added])

        if self.library.Sonarr and tvdb_paths:
            if "item_sonarr_tag" in self.item_details:
                self.library.Sonarr.edit_tags([t[0] if isinstance(t, tuple) else t for t in tvdb_paths], self.item_details["item_sonarr_tag"], self.item_details["apply_tags"])
            if self.sonarr_details["add_existing"]:
                added = self.library.Sonarr.add_tvdb(tvdb_paths, **self.sonarr_details)
                self.added_to_sonarr.extend([{"title": show.title, "id": show.tvdbId} for show in added])

        for rating_key in rating_keys:
            try:
                item = self.fetch_item(rating_key)
            except Failed as e:
                logger.error(e)
                continue
            self.library.edit_tags("label", item, remove_tags=[f"{overlay_name} Overlay"])
            og_image = os.path.join(overlay_folder, f"{rating_key}.png")
            if os.path.exists(og_image):
                self.library.upload_file_poster(item, og_image)
                os.remove(og_image)
            self.config.Cache.update_image_map(item.ratingKey, self.library.image_table_name, "", "")

    def load_collection(self):
        if not self.obj and self.smart_url:
            self.library.create_smart_collection(self.name, self.smart_type_key, self.smart_url)
        elif not self.obj and self.blank_collection:
            self.library.create_blank_collection(self.name)
        elif self.smart_label_collection:
            try:
                if not self.library.smart_label_check(self.name):
                    raise Failed
                smart_type, _, self.smart_url = self.build_filter("smart_label", self.smart_label, default_sort="random")
                if not self.obj:
                    self.library.create_smart_collection(self.name, smart_type, self.smart_url)
            except Failed:
                raise Failed(f"{self.Type} Error: Label: {self.name} was not added to any items in the Library")
        self.obj = self.library.get_playlist(self.name) if self.playlist else self.library.get_collection(self.name)
        if not self.exists:
            self.created = True

    def update_details(self):
        logger.info("")
        logger.separator(f"Updating Details of {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        if self.smart_url and self.smart_url != self.library.smart_filter(self.obj):
            self.library.update_smart_collection(self.obj, self.smart_url)
            logger.info(f"Detail: Smart Filter updated to {self.smart_url}")

        def get_summary(summary_method, summaries):
            logger.info(f"Detail: {summary_method} will update {self.Type} Summary")
            return summaries[summary_method]
        if "summary" in self.summaries:                     summary = get_summary("summary", self.summaries)
        elif "tmdb_description" in self.summaries:          summary = get_summary("tmdb_description", self.summaries)
        elif "letterboxd_description" in self.summaries:    summary = get_summary("letterboxd_description", self.summaries)
        elif "tmdb_summary" in self.summaries:              summary = get_summary("tmdb_summary", self.summaries)
        elif "tvdb_summary" in self.summaries:              summary = get_summary("tvdb_summary", self.summaries)
        elif "tmdb_biography" in self.summaries:            summary = get_summary("tmdb_biography", self.summaries)
        elif "tmdb_person" in self.summaries:               summary = get_summary("tmdb_person", self.summaries)
        elif "tmdb_collection_details" in self.summaries:   summary = get_summary("tmdb_collection_details", self.summaries)
        elif "trakt_list_details" in self.summaries:        summary = get_summary("trakt_list_details", self.summaries)
        elif "tmdb_list_details" in self.summaries:         summary = get_summary("tmdb_list_details", self.summaries)
        elif "letterboxd_list_details" in self.summaries:   summary = get_summary("letterboxd_list_details", self.summaries)
        elif "icheckmovies_list_details" in self.summaries: summary = get_summary("icheckmovies_list_details", self.summaries)
        elif "tmdb_actor_details" in self.summaries:        summary = get_summary("tmdb_actor_details", self.summaries)
        elif "tmdb_crew_details" in self.summaries:         summary = get_summary("tmdb_crew_details", self.summaries)
        elif "tmdb_director_details" in self.summaries:     summary = get_summary("tmdb_director_details", self.summaries)
        elif "tmdb_producer_details" in self.summaries:     summary = get_summary("tmdb_producer_details", self.summaries)
        elif "tmdb_writer_details" in self.summaries:       summary = get_summary("tmdb_writer_details", self.summaries)
        elif "tmdb_movie_details" in self.summaries:        summary = get_summary("tmdb_movie_details", self.summaries)
        elif "tvdb_movie_details" in self.summaries:        summary = get_summary("tvdb_movie_details", self.summaries)
        elif "tvdb_show_details" in self.summaries:         summary = get_summary("tvdb_show_details", self.summaries)
        elif "tmdb_show_details" in self.summaries:         summary = get_summary("tmdb_show_details", self.summaries)
        else:                                               summary = None

        if self.playlist:
            if summary and str(summary) != str(self.obj.summary):
                try:
                    self.obj.edit(summary=str(summary))
                    logger.info(f"Summary | {summary:<25}")
                    logger.info("Details: have been updated")
                except NotFound:
                    logger.error("Details: Failed to Update Please delete the collection and run again")
                logger.info("")
        else:
            self.obj.batchEdits()

            batch_display = "Collection Metadata Edits"
            if summary and str(summary) != str(self.obj.summary):
                self.obj.editSummary(summary)
                batch_display += f"\nSummary | {summary:<25}"

            if "sort_title" in self.details and str(self.details["sort_title"]) != str(self.obj.titleSort):
                self.obj.editSortTitle(self.details["sort_title"])
                batch_display += f"\nSort Title | {self.details['sort_title']}"

            if "content_rating" in self.details and str(self.details["content_rating"]) != str(self.obj.contentRating):
                self.obj.editContentRating(self.details["content_rating"])
                batch_display += f"\nContent Rating | {self.details['content_rating']}"

            add_tags = self.details["label"] if "label" in self.details else None
            remove_tags = self.details["label.remove"] if "label.remove" in self.details else None
            sync_tags = self.details["label.sync"] if "label.sync" in self.details else None
            batch_display += f"\n{self.library.edit_tags('label', self.obj, add_tags=add_tags, remove_tags=remove_tags, sync_tags=sync_tags, do_print=False)[28:]}"

            logger.info(batch_display)
            if len(batch_display) > 25:
                try:
                    self.obj.saveEdits()
                    logger.info("Details: have been updated")
                except NotFound:
                    logger.error("Details: Failed to Update Please delete the collection and run again")
                logger.info("")

            if "collection_mode" in self.details:
                self.library.collection_mode_query(self.obj, self.details["collection_mode"])

            if "collection_order" in self.details:
                if int(self.obj.collectionSort) not in plex.collection_order_keys\
                        or plex.collection_order_keys[int(self.obj.collectionSort)] != self.details["collection_order"]:
                    self.library.collection_order_query(self.obj, self.details["collection_order"])
                    logger.info(f"Collection Order | {self.details['collection_order']}")

            if "visible_library" in self.details or "visible_home" in self.details or "visible_shared" in self.details:
                visibility = self.library.collection_visibility(self.obj)
                visible_library = None
                visible_home = None
                visible_shared = None

                if "visible_library" in self.details and self.details["visible_library"] != visibility["library"]:
                    visible_library = self.details["visible_library"]

                if "visible_home" in self.details and self.details["visible_home"] != visibility["home"]:
                    visible_home = self.details["visible_home"]

                if "visible_shared" in self.details and self.details["visible_shared"] != visibility["shared"]:
                    visible_shared = self.details["visible_shared"]

                if visible_library is not None or visible_home is not None or visible_shared is not None:
                    self.library.collection_visibility_update(self.obj, visibility=visibility, library=visible_library, home=visible_home, shared=visible_shared)
                    logger.info("Collection Visibility Updated")

        poster_image = None
        background_image = None
        asset_location = None
        if self.library.asset_directory:
            name_mapping = self.name
            if "name_mapping" in self.details:
                if self.details["name_mapping"]:                    name_mapping = self.details["name_mapping"]
                else:                                               logger.error(f"{self.Type} Error: name_mapping attribute is blank")
            poster_image, background_image, asset_location = self.library.find_assets(
                self.obj, name=name_mapping, upload=False,
                folders=self.details["asset_folders"], create=self.details["create_asset_folders"]
            )
            if poster_image:
                self.posters["asset_directory"] = poster_image
            if background_image:
                self.backgrounds["asset_directory"] = background_image

        self.collection_poster = None
        if len(self.posters) > 0:
            logger.debug(f"{len(self.posters)} posters found:")
            for p in self.posters:
                logger.debug(f"Method: {p} Poster: {self.posters[p]}")

            if "url_poster" in self.posters:
                if self.library.download_url_assets and asset_location:
                    if poster_image:
                        self.collection_poster = self.posters["asset_directory"]
                    else:
                        response = self.config.get(self.posters["url_poster"], headers=util.header())
                        if response.status_code >= 400 or "Content-Type" not in response.headers or response.headers["Content-Type"] not in ["image/png", "image/jpeg"]:
                            logger.error(f"Image Error: Failed to parse Image at {self.posters['url_poster']}")
                        else:
                            new_image = os.path.join(asset_location, f"poster{'.png' if response.headers['Content-Type'] == 'image/png' else '.jpg'}")
                            with open(new_image, "wb") as handler:
                                handler.write(response.content)
                            self.collection_poster = ImageData("asset_directory", new_image, prefix=f"{self.obj.title}'s ", is_url=False)
                if not self.collection_poster:
                    self.collection_poster = ImageData("url_poster", self.posters["url_poster"])
            elif "file_poster" in self.posters:                 self.collection_poster = ImageData("file_poster", self.posters["file_poster"], is_url=False)
            elif "tmdb_poster" in self.posters:                 self.collection_poster = ImageData("tmdb_poster", self.posters["tmdb_poster"])
            elif "tmdb_profile" in self.posters:                self.collection_poster = ImageData("tmdb_poster", self.posters["tmdb_profile"])
            elif "tvdb_poster" in self.posters:                 self.collection_poster = ImageData("tvdb_poster", self.posters["tvdb_poster"])
            elif "asset_directory" in self.posters:             self.collection_poster = self.posters["asset_directory"]
            elif "tmdb_person" in self.posters:                 self.collection_poster = ImageData("tmdb_person", self.posters["tmdb_person"])
            elif "tmdb_collection_details" in self.posters:     self.collection_poster = ImageData("tmdb_collection_details", self.posters["tmdb_collection_details"])
            elif "tmdb_actor_details" in self.posters:          self.collection_poster = ImageData("tmdb_actor_details", self.posters["tmdb_actor_details"])
            elif "tmdb_crew_details" in self.posters:           self.collection_poster = ImageData("tmdb_crew_details", self.posters["tmdb_crew_details"])
            elif "tmdb_director_details" in self.posters:       self.collection_poster = ImageData("tmdb_director_details", self.posters["tmdb_director_details"])
            elif "tmdb_producer_details" in self.posters:       self.collection_poster = ImageData("tmdb_producer_details", self.posters["tmdb_producer_details"])
            elif "tmdb_writer_details" in self.posters:         self.collection_poster = ImageData("tmdb_writer_details", self.posters["tmdb_writer_details"])
            elif "tmdb_movie_details" in self.posters:          self.collection_poster = ImageData("tmdb_movie_details", self.posters["tmdb_movie_details"])
            elif "tvdb_movie_details" in self.posters:          self.collection_poster = ImageData("tvdb_movie_details", self.posters["tvdb_movie_details"])
            elif "tvdb_show_details" in self.posters:           self.collection_poster = ImageData("tvdb_show_details", self.posters["tvdb_show_details"])
            elif "tmdb_show_details" in self.posters:           self.collection_poster = ImageData("tmdb_show_details", self.posters["tmdb_show_details"])
        else:
            logger.info(f"No poster {self.type} detail or asset folder found")

        self.collection_background = None
        if len(self.backgrounds) > 0:
            logger.debug(f"{len(self.backgrounds)} backgrounds found:")
            for b in self.backgrounds:
                logger.debug(f"Method: {b} Background: {self.backgrounds[b]}")

            if "url_background" in self.backgrounds:
                if self.library.download_url_assets and asset_location:
                    if background_image:
                        self.collection_background = self.backgrounds["asset_directory"]
                    else:
                        response = self.config.get(self.backgrounds["url_background"], headers=util.header())
                        if response.status_code >= 400 or "Content-Type" not in response.headers or response.headers["Content-Type"] not in ["image/png", "image/jpeg"]:
                            logger.error(f"Image Error: Failed to parse Image at {self.backgrounds['url_background']}")
                        else:
                            new_image = os.path.join(asset_location, f"background{'.png' if response.headers['Content-Type'] == 'image/png' else '.jpg'}")
                            with open(new_image, "wb") as handler:
                                handler.write(response.content)
                            self.collection_background = ImageData("asset_directory", new_image, prefix=f"{self.obj.title}'s ", is_url=False, is_poster=False)
                if not self.collection_background:
                    self.collection_background = ImageData("url_background", self.backgrounds["url_background"], is_poster=False)
            elif "file_background" in self.backgrounds:         self.collection_background = ImageData("file_background", self.backgrounds["file_background"], is_poster=False, is_url=False)
            elif "tmdb_background" in self.backgrounds:         self.collection_background = ImageData("tmdb_background", self.backgrounds["tmdb_background"], is_poster=False)
            elif "tvdb_background" in self.backgrounds:         self.collection_background = ImageData("tvdb_background", self.backgrounds["tvdb_background"], is_poster=False)
            elif "asset_directory" in self.backgrounds:         self.collection_background = self.backgrounds["asset_directory"]
            elif "tmdb_collection_details" in self.backgrounds: self.collection_background = ImageData("tmdb_collection_details", self.backgrounds["tmdb_collection_details"], is_poster=False)
            elif "tmdb_movie_details" in self.backgrounds:      self.collection_background = ImageData("tmdb_movie_details", self.backgrounds["tmdb_movie_details"], is_poster=False)
            elif "tvdb_movie_details" in self.backgrounds:      self.collection_background = ImageData("tvdb_movie_details", self.backgrounds["tvdb_movie_details"], is_poster=False)
            elif "tvdb_show_details" in self.backgrounds:       self.collection_background = ImageData("tvdb_show_details", self.backgrounds["tvdb_show_details"], is_poster=False)
            elif "tmdb_show_details" in self.backgrounds:       self.collection_background = ImageData("tmdb_show_details", self.backgrounds["tmdb_show_details"], is_poster=False)
        else:
            logger.info(f"No background {self.type} detail or asset folder found")

        if self.collection_poster or self.collection_background:
            self.library.upload_images(self.obj, poster=self.collection_poster, background=self.collection_background)

        if self.url_theme:
            self.library.upload_theme(self.obj, url=self.url_theme)
        elif self.file_theme:
            self.library.upload_theme(self.obj, filepath=self.file_theme)

    def sort_collection(self):
        logger.info("")
        logger.separator(f"Sorting {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        if self.custom_sort is True:
            items = self.added_items
        else:
            plex_search = {"sort_by": self.custom_sort}
            if self.collection_level in ["season", "episode"]:
                plex_search["type"] = f"{self.collection_level}s"
                plex_search["any"] = {f"{self.collection_level}_collection": self.name}
            else:
                plex_search["any"] = {"collection": self.name}
            search_data = self.build_filter("plex_search", plex_search)
            items = self.library.get_filter_items(search_data[2])
        previous = None
        for i, item in enumerate(items, 0):
            if len(self.items) <= i or item.ratingKey != self.items[i].ratingKey:
                text = f"after {util.item_title(previous)}" if previous else "to the beginning"
                logger.info(f"Moving {util.item_title(item)} {text}")
                self.library.moveItem(self.obj, item, previous)
            previous = item

    def delete_user_playlist(self, title, user):
        user_server = self.library.PlexServer.switchUser(user)
        user_playlist = user_server.playlist(title)
        user_playlist.delete()

    def delete(self):
        output = ""
        if self.obj:
            self.library.query(self.obj.delete)
            output = f"{self.Type} {self.obj.title} deleted"
            if self.playlist:
                if self.valid_users:
                    for user in self.valid_users:
                        try:
                            self.delete_user_playlist(self.obj.title, user)
                            output += f"\nPlaylist {self.obj.title} deleted on User {user}"
                        except NotFound:
                            output += f"\nPlaylist {self.obj.title} not found on User {user}"
        return output

    def sync_playlist(self):
        if self.obj and self.valid_users:
            logger.info("")
            logger.separator(f"Syncing Playlist to Users", space=False, border=False)
            logger.info("")
            for user in self.valid_users:
                try:
                    self.delete_user_playlist(self.obj.title, user)
                except NotFound:
                    pass
                self.obj.copyToUser(user)
                logger.info(f"Playlist: {self.name} synced to {user}")

    def send_notifications(self, playlist=False):
        if self.obj and self.details["changes_webhooks"] and \
                (self.created or len(self.notification_additions) > 0 or len(self.notification_removals) > 0):
            self.obj.reload()
            try:
                self.library.Webhooks.collection_hooks(
                    self.details["changes_webhooks"],
                    self.obj,
                    poster_url=self.collection_poster.location if self.collection_poster and self.collection_poster.is_url else None,
                    background_url=self.collection_background.location if self.collection_background and self.collection_background.is_url else None,
                    created=self.created,
                    deleted=self.deleted,
                    additions=self.notification_additions,
                    removals=self.notification_removals,
                    radarr=self.added_to_radarr,
                    sonarr=self.added_to_sonarr,
                    playlist=playlist
                )
            except Failed as e:
                logger.stacktrace()
                logger.error(f"Webhooks Error: {e}")

    def run_collections_again(self):
        self.obj = self.library.get_collection(self.name)
        name, collection_items = self.library.get_collection_name_and_items(self.obj, self.smart_label_collection)
        self.created = False
        rating_keys = []
        amount_added = 0
        self.notification_additions = []
        self.added_to_radarr = []
        self.added_to_sonarr = []
        for mm in self.run_again_movies:
            if mm in self.library.movie_map:
                rating_keys.extend(self.library.movie_map[mm])
        if self.library.is_show:
            for sm in self.run_again_shows:
                if sm in self.library.show_map:
                    rating_keys.extend(self.library.show_map[sm])
        if len(rating_keys) > 0:
            for rating_key in rating_keys:
                try:
                    current = self.library.fetchItem(int(rating_key))
                except (BadRequest, NotFound):
                    logger.error(f"Plex Error: Item {rating_key} not found")
                    continue
                if current in collection_items:
                    logger.info(f"{name} {self.Type} | = | {util.item_title(current)}")
                else:
                    self.library.alter_collection(current, name, smart_label_collection=self.smart_label_collection)
                    amount_added += 1
                    logger.info(f"{name} {self.Type} | + | {util.item_title(current)}")
                    if self.library.is_movie and current.ratingKey in self.library.movie_rating_key_map:
                        add_id = self.library.movie_rating_key_map[current.ratingKey]
                    elif self.library.is_show and current.ratingKey in self.library.show_rating_key_map:
                        add_id = self.library.show_rating_key_map[current.ratingKey]
                    else:
                        add_id = None
                    self.notification_additions.append(util.item_set(current, add_id))
            self.send_notifications()
            logger.info(f"{len(rating_keys)} {self.collection_level.capitalize()}{'s' if len(rating_keys) > 1 else ''} Processed")

        if len(self.run_again_movies) > 0:
            logger.info("")
            for missing_id in self.run_again_movies:
                if missing_id not in self.library.movie_map:
                    try:
                        movie = self.config.TMDb.get_movie(missing_id)
                    except Failed as e:
                        logger.error(e)
                        continue
                    if self.details["show_missing"] is True:
                        current_title = f"{movie.title} ({movie.release_date.year})" if movie.release_date else movie.title
                        logger.info(f"{name} {self.Type} | ? | {current_title} (TMDb: {missing_id})")
            logger.info("")
            logger.info(f"{len(self.run_again_movies)} Movie{'s' if len(self.run_again_movies) > 1 else ''} Missing")

        if len(self.run_again_shows) > 0 and self.library.is_show:
            logger.info("")
            for missing_id in self.run_again_shows:
                if missing_id not in self.library.show_map:
                    try:
                        title = self.config.TVDb.get_series(missing_id).title
                    except Failed as e:
                        logger.error(e)
                        continue
                    if self.details["show_missing"] is True:
                        logger.info(f"{name} {self.Type} | ? | {title} (TVDb: {missing_id})")
            logger.info(f"{len(self.run_again_shows)} Show{'s' if len(self.run_again_shows) > 1 else ''} Missing")

        return amount_added
