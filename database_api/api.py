"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Any

from .core import *

if TYPE_CHECKING:
    pass

from flask import Flask, request
from sqlalchemy import event
import logging

from .route_sections import self_roles, messages

app = Flask(__name__)
logger = logging.getLogger("api")


@event.listens_for(engine, "connect")
def do_connect(dbapi_connection, connection_record):
    # disable pysqlite's emitting of the BEGIN statement entirely.
    # also stops it from emitting COMMIT before any DDL.
    dbapi_connection.isolation_level = None


@event.listens_for(engine, "begin")
def do_begin(conn):
    # emit our own BEGIN
    conn.exec_driver_sql("BEGIN")


@app.post("/aux")
def aux_query():
    query: str = request.json["query"]
    params: Tuple[Any] = request.json["params"]
    logger.warning(f"AUX api method called with {query} {params}")
    # yes i know this is unsafe, but it's only until this method is removed
    # TODO remove this
    current = 0
    param = 0
    while query.find("?", current + 1) != -1:
        current = query.find("?", current + 1)
        query = f"{query[:current]}{params[param]}{query[current + 1:]}"
        param += 1

    logger.warning(f" - transformed to {query}")
    session.execute(query)
    session.commit()
    return {}


@app.get("/ping")
def ping():
    return {}


self_roles.setup(app, engine, session)
messages.setup(app, engine, session)
