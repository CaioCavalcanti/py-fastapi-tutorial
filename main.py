from fastapi import FastAPI, Query, Path, Body, Cookie, Header
from enum import Enum
from typing import List, Optional, Set, Dict, Union
from uuid import UUID
from datetime import datetime, time, timedelta

from pydantic import BaseModel, Field, HttpUrl, EmailStr

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
    tax: float = 10.5
    tags: Set[str] = set()
    images: Optional[List[Image]] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2
            }
        }


class Offer(BaseModel):
    name: str = Field(..., example="Foo")
    description: Optional[str] = Field(None, example="A very nice offer")
    price: float = Field(..., example=35.7)
    items: List[Item]


class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


class User(UserBase):
    pass


class UserIn(UserBase):
    password: str


class UserOut(UserBase):
    pass


class UserInDb(UserBase):
    hashed_password: str


class BaseItem(BaseModel):
    description: str
    type: str


class CarItem(BaseItem):
    type = "car"


class PlaneItem(BaseItem):
    type = "plane"
    size = int


fake_items_db = [{"item_name": "Foo"}, {
    "item_name": "Bar"}, {"item_name": "Baz"}]


items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}

extra_items = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5
    }
}


def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password


def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDb(**user_in.dict(), hashed_password=hashed_password)
    print("User saved! ..not really")
    return user_in_db


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/items", response_model=Item)
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
    ),
    ads_id: Optional[str] = Cookie(None),
    user_agent: Optional[str] = Header(None),
    x_token: Optional[List[str]] = Header(None)
):
    paged_items = fake_items_db[skip: skip + limit]
    results = {"items": paged_items, "ads_id": ads_id,
               "User-Agent": user_agent, "X-Token values": x_token}
    if q:
        results.update({"q": q})
    return results


@app.get("/items/{item_id}", response_model=Item, response_model_exclude_unset=True)
async def read_item(
    *,
    item_id: str = Path(..., title="The ID of the item to get."),
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
    item = items[item_id]
    item.update({"needy": needy})
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"})

    return item


@app.put("/items/{item_id}/extra")
async def read_items_extra(
    item_id: UUID,
    start_datetime: Optional[datetime] = Body(None),
    end_datetime: Optional[datetime] = Body(None),
    repeat_at: Optional[time] = Body(None, example="20:53:11.173"),
    process_after: Optional[timedelta] = Body(None)
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_datetime
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "repeat_at": repeat_at,
        "process_after": process_after,
        "start_process": start_process,
        "duration": duration
    }


@app.get(
    "/items/{item_id}/name",
    response_model=Item,
    response_model_include={"name", "description"}
)
async def read_item_name(item_id: str):
    return items[item_id]


@app.get("/items/{item_id}/public", response_model=Item, response_model_exclude=["tax"])
async def read_item_public_data(item_id: str):
    return items[item_id]


@app.post("/users", response_model=UserOut)
async def create_user(user: UserIn):
    """
    Create an user.

    Here, even though our path operation function is returning the
    same input user that contains the password, we declared the
    response_model to be our model UserOut, that doesn't include
    the password.
    """
    user_saved = fake_save_user(user_in)
    return user_saved


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


@app.get("/extra-items/", response_model=List[Item])
async def read_extra_items():
    return items


@app.get("/extra-items/{item_id}", response_model=Union[PlaneItem, CarItem])
async def read_extra_item(item_id: str):
    return extra_items[item_id]

@app.get("/arbitrary-dict/", response_model=Dict[str, float])
async def read_arbitrary_dict():
    return {"foo": 2.3, "bar": 3.4}