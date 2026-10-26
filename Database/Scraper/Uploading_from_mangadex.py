from Database_creation import *


MANGADEX_API = "https://api.mangadex.org"

def get_mangadex_manga_id():
    query = text(
        'SELECT m.manga_surr_id, m.anilist_id, t.title_name '
        'FROM "Manga" m '
        'INNER JOIN "Title" t ON m.manga_surr_id = t.manga_id '
        'WHERE t.is_prime = TRUE and t.title_name IS NOT NULL'
    )
    mangadex_query = text("""SELECT source_surr_id FROM "Source" WHERE source_name = 'mangadex'""")
    with Session(engine) as session:
        rows = session.execute(query).mappings().all()
        mangadex_source_id = session.execute(mangadex_query).scalar_one()

    results = []


    with httpx.Client(timeout=30) as client:
        for row in rows:
            anilist_id = str(row["anilist_id"])
            title = row["title_name"]

            if not title:
                continue

            try:
                response = client.get(
                    f"{MANGADEX_API}/manga",
                    params={
                        "title": title,
                        "limit": 100,
                    },
                )
                response.raise_for_status()

                manga_results = response.json().get("data", [])

                for manga in manga_results:
                    links = manga["attributes"].get("links") or {}

                    if str(links.get("al", "")) == anilist_id:
                        mangadex_id = manga["id"]
                        break

                results.append({
                    "manga_id": row["manga_surr_id"],
                    'src_id': mangadex_source_id,
                    "manga_src_id": mangadex_id,
                    "last_synced_at": datetime.now(timezone.utc),
                })

                print(f"{title} -> {mangadex_id or 'No match found'}")

            except httpx.HTTPError as e:
                print(f"Request failed for '{title}': {e}")

            time.sleep(0.25)

    return results


def deliver_manga_sources():
    data = get_mangadex_manga_id()

    if not data:
        print("No MangaDex matches to upload.")
        return

    data = [row for row in data if row["src_id"] is not None]

    if not data:
        print("No verified MangaDex matches to upload.")
        return

    stmt = insert(MangaSources).values(data)
    stmt = stmt.on_conflict_do_nothing()

    with Session(engine) as session:
        session.execute(stmt)
        session.commit()

    print(f"Processed {len(data)} records.")

