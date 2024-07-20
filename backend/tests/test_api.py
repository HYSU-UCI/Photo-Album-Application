import os
from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import Response

IMAGES_PATH = [
    "tests/images/a.jpg",
    "tests/images/b.jpg",
]

BAD_TAG = "00000000-0000-0000-0000-000000000000"

pytestmark = pytest.mark.anyio


async def create_image(client: AsyncClient, image_path: str, raw: bool = False) -> dict | Response:
    with open(image_path, "rb") as f:
        response = await client.post("/api/v1/images/create", files={"image": f})
    if raw:
        return response
    assert response.status_code == status.HTTP_201_CREATED
    assert UUID(response.json()["id"])
    assert response.json()["filename"] == os.path.basename(image_path)
    assert response.json()["mime_type"] == "image/jpeg"
    return response.json()


async def view_raw_image(client: AsyncClient, image_id: str) -> Response:
    return await client.get(f"/view/images/{image_id}")


async def delete_image(client: AsyncClient, image_id: str) -> Response:
    return await client.delete(f"/api/v1/images/{image_id}")


async def add_tag_to_image(
    client: AsyncClient, image_id: str, tag_name: str, raw: bool = False
) -> dict | Response:
    response = await client.post(f"/api/v1/images/{image_id}/tags", json={"name": tag_name})
    if raw:
        return response
    assert response.status_code == status.HTTP_201_CREATED
    assert UUID(response.json()["id"])
    assert response.json()["name"] == tag_name
    return response.json()


async def replace_tag_of_image(
    client: AsyncClient, image_id: str, tag_id: str, new_tag_name: str, raw: bool = False
) -> dict | Response:
    response = await client.put(
        f"/api/v1/images/{image_id}/tags", json={"id": tag_id, "name": new_tag_name}
    )
    if raw:
        return response
    assert response.status_code == status.HTTP_200_OK
    assert UUID(response.json()["id"])
    assert response.json()["name"] == new_tag_name
    return response.json()


async def delete_tag_of_image(client: AsyncClient, image_id: str, tag_id: str) -> Response:
    return await client.delete(f"/api/v1/images/{image_id}/tags/{tag_id}")


async def get_tags_list(client: AsyncClient) -> list:
    response = await client.get("/api/v1/tags/list")
    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def get_images_list(client: AsyncClient, offset: int = None, limit: int = None) -> list:
    params = {}
    if offset is not None:
        params["offset"] = offset
    if limit is not None:
        params["limit"] = limit
    response = await client.get("/api/v1/images/list", params=params)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def get_image_metadata(
    client: AsyncClient, image_id: str, raw: bool = False
) -> dict | Response:
    response = await client.get(f"/api/v1/images/{image_id}")
    if raw:
        return response
    assert response.status_code == status.HTTP_200_OK
    assert "tags" in response.json()
    assert response.json()["filename"]
    return response.json()


async def search_images_by_tags(client: AsyncClient, tags: list) -> list:
    return (await client.post("/api/v1/images/search", json={"tags_id": tags})).json()


async def test_health(client: AsyncClient):
    assert (await client.get("/")).status_code == status.HTTP_200_OK


async def test_create_and_delete_and_view_image(client: AsyncClient):
    image_path = IMAGES_PATH[0]

    # create
    image = await create_image(client, image_path)

    # view
    response = await view_raw_image(client, image["id"])
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/jpeg"
    with open(image_path, "rb") as f:
        assert response.content == f.read()

    # delete
    response = await delete_image(client, image["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # make sure view returns 404 after deletion
    response = await view_raw_image(client, image["id"])
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_upload_fail_gracefully(client: AsyncClient):
    # make sure upload fails with non-image
    response = await client.post(
        "/api/v1/images/create",
        files={"image": ("evil.html", b"<svg/onload=alert(1)>", "text/html")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_delete_and_view_image_fail_gracefully(client: AsyncClient):
    # make sure view and delete fail with bad image id
    response = await view_raw_image(client, BAD_TAG)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = await delete_image(client, BAD_TAG)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_add_and_replace_and_delete_and_view_tags(client: AsyncClient):
    # create image
    images = []
    for image_path in IMAGES_PATH:
        images.append(await create_image(client, image_path))

    # add tag a to image[0]
    tag_a = await add_tag_to_image(client, images[0]["id"], "a")

    # add tag a to image[1]
    tag_b = await add_tag_to_image(client, images[1]["id"], "a")

    # view all tags
    tags = await get_tags_list(client)
    assert len(tags) == 1 and tags[0] == tag_a

    # add tag b to image[0]
    tag_b = await add_tag_to_image(client, images[0]["id"], "b")

    # view all tags
    tags = await get_tags_list(client)
    assert len(tags) == 2 and tag_a in tags and tag_b in tags

    # replace tag b with tag c in image[0]
    tac_c = await replace_tag_of_image(client, images[0]["id"], tag_b["id"], "c")

    # view all tags
    tags = await get_tags_list(client)
    assert len(tags) == 2 and tag_a in tags and tac_c in tags

    # delete tag c of image[0]
    response = await delete_tag_of_image(client, images[0]["id"], tac_c["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # view all tags
    tags = await get_tags_list(client)
    assert len(tags) == 1 and tags[0] == tag_a

    # delete tag a of image[0]
    response = await delete_tag_of_image(client, images[0]["id"], tag_a["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # view all tags
    tags = await get_tags_list(client)
    assert len(tags) == 1 and tags[0] == tag_a

    # delete tag a of image[1]
    response = await delete_tag_of_image(client, images[1]["id"], tag_a["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # view all tags
    tags = await get_tags_list(client)
    assert len(tags) == 0


async def test_delete_image_and_orphan_tags(client: AsyncClient):
    # create image a
    image_a = await create_image(client, IMAGES_PATH[0])

    # create image b
    image_b = await create_image(client, IMAGES_PATH[1])

    # add tag a to image a
    tag_a = await add_tag_to_image(client, image_a["id"], "a")

    # add tag a to image b
    await add_tag_to_image(client, image_b["id"], "a")

    # get all tags
    tags = await get_tags_list(client)
    assert len(tags) == 1 and tags[0] == tag_a

    # add tag b to image b
    tag_b = await add_tag_to_image(client, image_b["id"], "b")

    # get all tags
    tags = await get_tags_list(client)
    assert len(tags) == 2 and tag_a in tags and tag_b in tags

    # delete image b
    response = await delete_image(client, image_b["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # get all tags
    tags = await get_tags_list(client)
    assert len(tags) == 1 and tags[0] == tag_a

    # delete image a
    response = await delete_image(client, image_a["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # get all tags
    tags = await get_tags_list(client)
    assert len(tags) == 0


async def test_replace_and_delete_tags_fail_gracefully(client: AsyncClient):
    # replace and delete with bad image id
    response = await client.put(f"/api/v1/images/{BAD_TAG}/tags", json={"id": BAD_TAG, "name": "a"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response = await client.delete(f"/api/v1/images/{BAD_TAG}/tags/{BAD_TAG}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    image = await create_image(client, IMAGES_PATH[0])

    # replace and delete with bad tag id
    response = await client.put(
        f"/api/v1/images/{image['id']}/tags", json={"id": BAD_TAG, "name": "a"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response = await client.delete(f"/api/v1/images/{image['id']}/tags/{BAD_TAG}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    tag_a = await add_tag_to_image(client, image["id"], "a")
    tag_b = await add_tag_to_image(client, image["id"], "b")

    # replace tag with existing tag
    response = await replace_tag_of_image(client, image["id"], tag_a["id"], "a", raw=True)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response = await replace_tag_of_image(client, image["id"], tag_b["id"], "a", raw=True)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_list_images(client: AsyncClient):
    # list images
    images = await get_images_list(client)
    assert len(images) == 0

    # create image a
    image_a = await create_image(client, IMAGES_PATH[0])

    # list images
    images = await get_images_list(client)
    assert len(images) == 1 and images[0] == image_a

    # create image b
    image_b = await create_image(client, IMAGES_PATH[1])

    # list images
    images = await get_images_list(client)
    assert len(images) == 2 and image_a in images and image_b in images

    # delete image a
    response = await delete_image(client, image_a["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # list images
    images = await get_images_list(client)
    assert len(images) == 1 and image_b in images

    # delete image b
    response = await delete_image(client, image_b["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # list images
    images = await get_images_list(client)
    assert len(images) == 0

    uploaded_images = []
    for _ in range(40):
        uploaded_images.append(await create_image(client, IMAGES_PATH[0]))

    # list images (default 0 ~ 20)
    images = await get_images_list(client)
    assert len(images) == 20 and images == uploaded_images[:20]

    # list images
    images = await get_images_list(client, offset=10)
    assert len(images) == 20 and images == uploaded_images[10:30]

    images = await get_images_list(client, limit=100)
    assert len(images) == 40 and images == uploaded_images


async def test_get_image_metadata(client: AsyncClient):
    # create image
    image = await create_image(client, IMAGES_PATH[0])

    # get metadata
    metadata = await get_image_metadata(client, image["id"])
    assert metadata["filename"] == image["filename"]
    assert len(metadata["tags"]) == 0

    # add tag a to image
    tag_a = await add_tag_to_image(client, image["id"], "a")

    # get metadata
    metadata = await get_image_metadata(client, image["id"])
    assert metadata["filename"] == image["filename"]
    assert len(metadata["tags"]) == 1 and metadata["tags"][0] == tag_a

    # add tag b to image
    tag_b = await add_tag_to_image(client, image["id"], "b")

    # get metadata
    metadata = await get_image_metadata(client, image["id"])
    assert metadata["filename"] == image["filename"]
    assert len(metadata["tags"]) == 2 and tag_a in metadata["tags"] and tag_b in metadata["tags"]

    # delete tag a of image
    response = await delete_tag_of_image(client, image["id"], tag_a["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # get metadata
    metadata = await get_image_metadata(client, image["id"])
    assert metadata["filename"] == image["filename"]
    assert len(metadata["tags"]) == 1 and tag_b in metadata["tags"]

    # replace tag b of image with tag c
    tag_c = await replace_tag_of_image(client, image["id"], tag_b["id"], "c")

    # get metadata
    metadata = await get_image_metadata(client, image["id"])
    assert metadata["filename"] == image["filename"]
    assert len(metadata["tags"]) == 1 and tag_c in metadata["tags"]

    # delete tag c of image
    response = await delete_tag_of_image(client, image["id"], tag_c["id"])
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # get metadata
    metadata = await get_image_metadata(client, image["id"])
    assert metadata["filename"] == image["filename"]
    assert len(metadata["tags"]) == 0


async def test_image_data_fail_gracefully(client: AsyncClient):
    assert (
        await get_image_metadata(client, BAD_TAG, raw=True)
    ).status_code == status.HTTP_404_NOT_FOUND


async def test_search_image(client: AsyncClient):
    # create image a
    image_a = await create_image(client, IMAGES_PATH[0])

    # create image b
    image_b = await create_image(client, IMAGES_PATH[1])

    # add tag a to image a
    tag_a = await add_tag_to_image(client, image_a["id"], "a")

    # add tag b to image a
    tag_b = await add_tag_to_image(client, image_a["id"], "b")

    # add tag a to image b
    await add_tag_to_image(client, image_b["id"], "a")  # Note: no need to save the tag

    # add tag c to image b
    tag_c = await add_tag_to_image(client, image_b["id"], "c")

    # search images by tag a
    images = await search_images_by_tags(client, [tag_a["id"]])
    assert len(images) == 2 and image_a in images and image_b in images

    # search images by tag b
    images = await search_images_by_tags(client, [tag_b["id"]])
    assert len(images) == 1 and image_a in images

    # search images by tag c
    images = await search_images_by_tags(client, [tag_c["id"]])
    assert len(images) == 1 and image_b in images

    # search images by tag a and tag b
    images = await search_images_by_tags(client, [tag_a["id"], tag_b["id"]])
    assert len(images) == 1 and image_a in images

    # search images by tag a and tag c
    images = await search_images_by_tags(client, [tag_a["id"], tag_c["id"]])
    assert len(images) == 1 and image_b in images

    # search images by tag a and tag b and tag c
    images = await search_images_by_tags(client, [tag_a["id"], tag_b["id"], tag_c["id"]])
    assert len(images) == 0
