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
from typing import Tuple, Dict, Union

from flask import Flask, request
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session


def setup(app: Flask, connection: Connection, session: Session):
    @app.get("/messages/greet/<int:guild_id>")
    def get_greet_message(guild_id: int):
        res = connection.execute("select welcome, welcome_channel, welcome_delete from messages where guild=?",
                                 (guild_id,)).fetchone()
        if not res:
            res = setup_default_messages(guild_id)[0]
        return {
            "results": [res[0], res[1], res[2]]
        }

    @app.get("/messages/leave/<int:guild_id>")
    def get_leave_message(guild_id: int):
        res = connection.execute("select goodbye, goodbye_channel, goodbye_delete from messages where guild=?",
                                 (guild_id,)).fetchone()
        if not res:
            res = setup_default_messages(guild_id)[1]
        return {
            "results": [res[0], res[1], res[2]]
        }

    @app.patch("/messages/greet/<int:guild_id>")
    def update_greet_message(guild_id: int):
        res = connection.execute("select welcome, welcome_channel, welcome_delete from messages where guild=?",
                                 (guild_id,)).fetchone() or setup_default_messages(guild_id)[0]
        res = update_message(request.json, res)
        connection.execute("update messages set welcome=?, welcome_channel=?, welcome_delete=? where guild=?",
                           res[0], res[1], res[2], guild_id)
        session.commit()
        return {"results": True}

    @app.patch("/messages/leave/<int:guild_id>")
    def update_leave_message(guild_id: int):
        res = connection.execute("select goodbye, goodbye_channel, goodbye_delete from messages where guild=?",
                                 (guild_id,)).fetchone() or setup_default_messages(guild_id)[0]
        res = update_message(request.json, res)
        connection.execute("update messages set goodbye=?, goodbye_channel=?, goodbye_delete=? where guild=?",
                           res[0], res[1], res[2], guild_id)
        session.commit()
        return {"results": True}

    def setup_default_messages(guild_id: int) -> Tuple[Tuple[str, int, int], Tuple[str, int, int]]:
        connection.execute("insert into messages values (?,?,?,?,?,?,?)",
                           (guild_id,
                            "&user_name; has joined the server", 0, 0,
                            "&user_name; has left the server", 0, 0
                            ))
        session.commit()
        return (
            ("&user_name; has joined the server", 0, 0),
            ("&user_name; has left the server", 0, 0)
        )

    def update_message(json: Dict[str, Union[str, int]], current: Tuple[str, int, int]) -> Tuple[str, int, int]:
        return (
            json.get("message", None) or current[0],
            json["channel"] if ("channel" in json and json["channel"] is not None) else current[1],
            json.get("delete", None) or current[2]
        )
