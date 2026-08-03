# API operations

## Creatives and dictionaries

```text
creatives search [filters] [--limit N] [--all-pages --max-pages N]
creatives get ID
dictionaries categories
dictionaries countries|languages [cursor options]
```

Search and detail records include media, text, dates, geo, languages,
placements, Meta Page, target app/link, host/IP, EU reach, favorites, blacklist,
cloaking, keywords, and categories.

## Favorites

```text
favorites list [search filters]
favorites add AD_ID --yes
favorites remove AD_ID --yes
favorites toggle AD_ID --yes
```

List first and confirm the exact ad ID before changing state.

## Blacklist

```text
blacklist rules [--attribute ATTR] [--value TEXT]
blacklist direct [cursor options]
blacklist affected ATTR VALUE [--include-direct] [cursor options]
blacklist add-rule AD_ID ATTR --yes
blacklist remove-rule ATTR VALUE --yes
blacklist clear-ad AD_ID --yes
```

Attributes: `AppId`, `FbPageId`, `Hostname`, `IpAddress`. A rule can affect many
ads. Read `blacklist affected` before removing it.

## Apps

```text
apps search [--name TEXT] [--platform Android|IOs]
            [--status alive|banned] [--from DATE --to DATE]
```

Apps use the AdWall stats endpoint and return app availability plus first/last
appearance and ad/page totals.

## Archives

```text
archives list
archives create URL [--country ISO] --yes
archives retry ARCHIVE_ID --yes
```

Creating an archive starts an external job and may consume plan resources.

## Raw

```text
raw api|stats|proxies|admin QUERY.graphql
    [--variables JSON | --variables-file FILE] [--yes]
```

Use only for an observed first-party operation. Do not probe admin mutations,
guess operations, bypass subscriptions, or send secrets in variables.
