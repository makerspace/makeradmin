Webshop
-------
A frontend and backend for a simple makerspace webshop.

The Docker container starts two scripts, `frontend.py` and `backend.py`.
The frontend hosts the webshop frontend on port 8011 and the backend registers with the
api-gateway as a normal service with the endpoint `webshop`.

To unify this with the rest of the makeradmin frontend a reverse proxy (e.g nginx) needs to be used.

The frontend uses SASS (.scss) stylesheets. These will be automatically compiled when the container starts and additionally if the APP_DEBUG environment variable is 'true' then it will continously watch for changes to the scss files and recompile them whenever they are changed.

To see all routes of the service, access the /path/to/service/routes endpoint which will list them all.