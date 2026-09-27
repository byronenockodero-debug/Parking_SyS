"""
The `backend` package is the web server: Flask routes and the database
layer. It is intentionally "thin" - it never implements algorithms
itself, it only calls into the `logic` package and renders templates.
"""
