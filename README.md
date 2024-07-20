
# Photo-Album-Application
## How to run

```bash
docker-compose up
```

Then visit `http://localhost:8000`

## Development

### Install some dependencies for development

```bash
pip install -r dev-requirements.txt
```

### Local testing

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Then visit `http://localhost:8000` for testing production environment and `http://localhost:8002` for testing backend.

### Unit tests for backend

```bash
$ docker-compose run --rm backend bash -c 'python -m pytest --verbose'
[+] Running 1/0
 ✔ Container online-image-manager-db-1  Running                                                0.0s
======================================= test session starts ========================================
platform linux -- Python 3.10.11, pytest-7.3.1, pluggy-1.0.0 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /app
plugins: asyncio-0.21.0, anyio-3.7.0
asyncio: mode=strict
collected 11 items

tests/test_api.py::test_health[asyncio+uvloop] PASSED                                        [  9%]
tests/test_api.py::test_create_and_delete_and_view_image[asyncio+uvloop] PASSED              [ 18%]
tests/test_api.py::test_upload_fail_gracefully[asyncio+uvloop] PASSED                        [ 27%]
tests/test_api.py::test_delete_and_view_image_fail_gracefully[asyncio+uvloop] PASSED         [ 36%]
tests/test_api.py::test_add_and_replace_and_delete_and_view_tags[asyncio+uvloop] PASSED      [ 45%]
tests/test_api.py::test_delete_image_and_orphan_tags[asyncio+uvloop] PASSED                  [ 54%]
tests/test_api.py::test_replace_and_delete_tags_fail_gracefully[asyncio+uvloop] PASSED       [ 63%]
tests/test_api.py::test_list_images[asyncio+uvloop] PASSED                                   [ 72%]
tests/test_api.py::test_get_image_metadata[asyncio+uvloop] PASSED                            [ 81%]
tests/test_api.py::test_image_data_fail_gracefully[asyncio+uvloop] PASSED                    [ 90%]
tests/test_api.py::test_search_image[asyncio+uvloop] PASSED                                  [100%]

======================================= 11 passed in 39.92s ========================================
```

### Lint

```shell
$ ./lint.sh --help
Usage: ./lint.sh [-f|--format]
  -f,  --format         format code instead of just checking the format
```
