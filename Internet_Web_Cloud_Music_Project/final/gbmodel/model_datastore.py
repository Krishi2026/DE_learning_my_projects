from google.cloud import datastore
from gbmodel.Model import Model

def from_datastore(entity):
    """Format datastore entity for application use."""
    if not entity:
        return None
    return {
        "title": entity.get("title"),
        "description": entity.get("description"),
        "weather": entity.get("weather"),
        "url": entity.get("url"),
        "image_url": entity.get("image_url"),
        "type": entity.get("type", "Playlist"),
        "user": entity.get("user"),
    }

class model(Model):
    def __init__(self):
        """
        Initializes the Cloud Datastore client for interacting with the database.
        """
        self.client = datastore.Client("cloud-chava-kchava")

    def select(self):
        """Fetch all playlists stored in the database."""
        query = self.client.query(kind="PlaylistEntry")
        entities = list(query.fetch())
        return list(map(from_datastore, entities))

    def insert(self, title, description, weather, url, image_url, type="Playlist", user=None):
        """Insert a playlist entry into the database."""
        key = self.client.key("PlaylistEntry")
        entity = datastore.Entity(key)
        entity.update({
            "title": title,
            "description": description,
            "weather": weather,
            "url": url,
            "image_url": image_url,
            "type": type,
            "user": user,
        })
        self.client.put(entity)
