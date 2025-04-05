from flask import render_template
from flask.views import MethodView

class Index(MethodView):
    """
    Handle GET requests for rendering the index page.
    """
    def get(self):
        """
        Render the index.html template, which displays a form for user input.

        Returns:
            str: Rendered HTML for the index page.
        """
        # Render the form for user input
        return render_template('index.html')
