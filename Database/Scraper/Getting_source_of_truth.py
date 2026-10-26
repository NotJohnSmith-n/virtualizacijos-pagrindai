from Database_creation import *

QUERY0 = """
query {
  GenreCollection
  MediaTagCollection {
    name
    description
    isAdult
  }
}
"""

QUERY1 = '''query {
  Page(page: 1, perPage: 50) {
    pageInfo {
      hasNextPage
    }
    media(type: MANGA, sort: [POPULARITY_DESC, SCORE_DESC]) {
      id
      title {
        romaji
        english
        native
      }
      status
      description
      genres
      isAdult
      startDate {
        year
      }
      countryOfOrigin
      tags {
        name
      }
    }
  }
}'''

LANGUAGES =  [
    {'language_code': 'JP', 'language_name': 'Japanese'},
    {'language_code': 'KR', 'language_name': 'Korean'},
    {'language_code': 'ZH-CN', 'language_name': 'Chinese'},
    {'language_code': 'ZH-TW', 'language_name': 'Chinese'}
]

SOURCES = [{'source_name' : 'mangadex', 'source_rank': 1}]

def deliver_sources():
    try:
        with Session(engine) as session:
            session.execute(insert(Source).values(SOURCES).on_conflict_do_nothing(index_elements=["source_name"]))
            session.commit()
            print("Sources uploaded successfully!")
    except Exception as e:
        print(f'Something went wrong with uploading sources! {e}')
        session.rollback()


def fetch_tags():
    rename = {'name': 'tag_name',
              'description' : 'tag_description',
              'isAdult' : 'is_adult'}

    r = httpx.post("https://graphql.anilist.co", json={"query": QUERY0}, timeout=30)
    r.raise_for_status()
    body = r.json()
    if "errors" in body:
        raise RuntimeError(body["errors"])
    data = body["data"]
    tags, genres = [{rename.get(k, k): v for k, v in value.items()} for value in data["MediaTagCollection"]],  [{'tag_name' : g} for g in data["GenreCollection"] if g]
    return tags, genres



def deliver_tags():
    tags, genres = fetch_tags()

    with Session(engine) as session:
        try:
            session.execute(insert(Tag).values(genres).on_conflict_do_nothing(index_elements=["tag_name"]))
            session.commit()
        except Exception as e:
            print(f'An error occurred, could not upload first batch of tags! {e}')
            session.rollback()
        try:
            stmt = insert(Tag).values(tags)

            stmt = stmt.on_conflict_do_update(
                index_elements=["tag_name"],
                set_={
                    'tag_description': stmt.excluded.tag_description,
                    'is_adult' : stmt.excluded.is_adult
                }
            )
            session.execute(stmt)
            session.commit()

            print("Tags uploaded successfully!")
        except Exception as e:
            print(f'An error occurred, could not upload second batch of tags! {e}')
            session.rollback()


def deliver_languages():
    try:
        with Session(engine) as session:
            session.execute(insert(Language).values(LANGUAGES).on_conflict_do_nothing(index_elements=["language_code"]))
            session.commit()
            print("Languages uploaded successfully!")
    except Exception as e:
        print(f'Something went wrong with uploading languages! {e}')
        session.rollback()




def get_caches():
    with Session(engine) as session:
        lang_result = session.execute(text('SELECT language_surr_id, language_code FROM "Language"'))
        tag_result = session.execute(text('SELECT tag_surr_id, tag_name FROM "Tag"'))
    lang_cache = {language.language_code: language.language_surr_id for language in lang_result}
    tag_cache = {tag.tag_name: tag.tag_surr_id for tag in tag_result}
    return lang_cache, tag_cache


def tranform_manga_row(row, lang_cache, tag_cache):
    rename = {
        "id": "anilist_id",
        "description": "manga_description",
        "isAdult": "is_adult",
        "status": "is_completed",
        "countryOfOrigin": "manga_original_language_id",
        "startDate": "manga_release_year"
    }

    row = {rename.get(k, k): v for k, v in row.items()}
    row["anilist_id"] = str(row["anilist_id"])
    row["is_completed"] = row["is_completed"] == "FINISHED"
    row["manga_release_year"] = (row.get("manga_release_year") or {}).get("year")
    row["manga_original_language_id"] = lang_cache.get(row["manga_original_language_id"])
    row["last_updated"] = datetime.now(timezone.utc)
    row['tags'] = [tag_cache.get(name) for name in [value.get('name') for value in row['tags'] if value.get('name')] if tag_cache.get(name)] + [tag_cache.get(name) for name in row['genres'] if name and tag_cache.get(name)]
    return row




def fetch_manga():
    r = httpx.post("https://graphql.anilist.co", json={"query": QUERY1}, timeout=30)
    r.raise_for_status()
    body = r.json()
    if "errors" in body:
        raise RuntimeError(body["errors"])
    data = body["data"]['Page']['media']
    lang_cache, tag_cache = get_caches()
    for i in range(len(data)):
        data[i] = tranform_manga_row(data[i], lang_cache, tag_cache)
    return data



def deliver_mangas():
    rows = fetch_manga()
    print(rows)
    if not rows:
        return
    columns = set(Manga.__table__.columns.keys())
    update_cols = (set(rows[0]) & columns) - {"anilist_id"}

    stmt = insert(Manga)
    stmt = stmt.on_conflict_do_update(
        index_elements=["anilist_id"],
        set_={c: stmt.excluded[c] for c in update_cols},
    ).returning(Manga.anilist_id, Manga.manga_surr_id)

    with Session(engine) as session, session.begin():
        ids = dict(session.execute(stmt, rows).all())

        tag_links = [
            {"manga_id": ids[r["anilist_id"]], "tag_id": tag_id}
            for r in rows for tag_id in r["tags"]
        ]

        if tag_links:
            session.execute(insert(MangaTag).on_conflict_do_nothing(), tag_links)

        title_links = [
            {
                "manga_id": ids[str(r["anilist_id"])],
                "title_name": title_value,
                "is_prime": language == "english",
            }
            for r in rows
            for language, title_value in (r.get("title") or {}).items()
            if title_value
        ]

        if title_links:
            session.execute(
                insert(Title).on_conflict_do_nothing(),
                title_links
            )



# with Session(engine) as session:
#     query = text('SELECT * FROM "Manga_Sources"')
#     response = session.execute(query)
#     for row in response:
#         print(row)

