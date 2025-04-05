class Model:
    def select(self):
        """Fetch all entries from the database."""
        raise NotImplementedError("Subclasses must implement this method.")

    def insert(self, *args):
        """Insert an entry into the database."""
        raise NotImplementedError("Subclasses must implement this method.")

    def update(self, *args):
        """Update an entry in the database."""
        raise NotImplementedError("Subclasses must implement this method.")

    def delete(self, *args):
        """Delete an entry from the database."""
        raise NotImplementedError("Subclasses must implement this method.")
