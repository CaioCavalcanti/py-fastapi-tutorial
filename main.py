from fastapi import FastAPI, Query, Path, Body
from enum import Enum
from typing import List, Optional, Set, Dict
from pydantic import BaseModel, Field, HttpUrl

app = FastAPI()


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: Optional[str] = Field(
        None,
        title="The description of the item",
        max_length=300
    )
    price: float = Field(
        ...,
        gt=0,
        description="The price must be greater than zero"
    )
    tax: Optional[float] = None
    tags: Set[str] = set()
    images: Optional[List[Image]] = None


class Offer(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    items: List[Item]


class User(BaseModel):
    username: str
    full_name: Optional[str] = None


fake_items_db = [{"item_name": "Foo"}, {
    "item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/items")
async def create_item(item: Item = Body(..., embed=True), q: Optional[str] = None):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, user: User, importance: int = Body(..., gt=0), q: Optional[str] = None):
    result = {"item_id": item_id, "user": user,
              "importance": importance, **item.dict()}
    if q:
        result.update({"q": q})
    return result


@app.get("/items/")
async def read_item(
    skip: int = 0,
    limit: int = 10,
    q: Optional[List[str]] = Query(
        ["foo", "bar"],
        alias="item-query",
        title="Query string",
        description="Query string for the items to search in the database that have a good match.",
        min_length=3,
        deprecated=True
    )
):
    paged_items = fake_items_db[skip: skip + limit]
    results = {"items": paged_items}
    if q:
        results.update({"q": q})
    return results


@app.get("/items/{item_id}")
async def read_item(
    *,
    item_id: int = Path(..., title="The ID of the item to get.",
                        ge=1, le=1000),
    needy: str,
    q: Optional[str] = Query(..., min_length=3),
    short: bool = False
):
    """
    Get an item with the given item_id.

    The Optional in Optional[str] is not used by FastAPI (FastAPI will
    only use the str part), but the Optional[str] will let your editor
    help you finding errors in your code.
    """
    item = {"item_id": item_id, "needy": needy}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"})

    return item


@app.get("/users/me")
async def read_user_me():
    """
    Get data about the current user.

    Order matters: because path operations are evaluated in order, you
    need to make sure that the path for /users/me is declared before the
    one for /users/{user_id}:
    """
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


@app.get("/users/{user_id}/items/{items_id}")
async def read_user_items(user_id: str, item_id: str, q: Optional[str] = None, short: bool = False):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer


@app.post("/images/multiple/")
async def create_multiple_images(images: List[Image]):
    return images

@app.post("/index-weights/")
async def create_intex_weights(weights: Dict[int, float]):
    return weights