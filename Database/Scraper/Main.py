from Getting_source_of_truth import deliver_sources, deliver_tags, deliver_languages, deliver_mangas
from Uploading_from_mangadex import deliver_manga_sources
from Database_creation import Base, engine

def updating_database():
    Base.metadata.create_all(engine)
    deliver_sources()
    deliver_tags()
    deliver_languages()
    deliver_mangas()
    deliver_manga_sources()

updating_database()

